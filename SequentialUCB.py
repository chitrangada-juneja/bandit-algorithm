
from collections import defaultdict
import numpy as np
import ollama

class SequentialUCB:
    def __init__(self, strategies, budget=1.0, lambda_value=0.5, alpha=3.0):
        self.strategies = strategies
        self.n_arms = len(strategies)
        self.budget = budget
        self.lambda_t = lambda_value
        self.alpha = alpha

        # Track performance of each individual strategy
        self.utilities = defaultdict(list)
        self.costs = defaultdict(list)
        self.T = defaultdict(int)
        self.time_step = 0

    def compute_ucb(self, arm):
        """Standard UCB computation"""
        if self.T[arm] == 0:
            return float('inf')

        net_rewards = [
            u - self.lambda_t * c
            for u, c in zip(self.utilities[arm], self.costs[arm])
        ]

        mean = np.mean(net_rewards)

        if self.T[arm] > 1:
            variance = np.var(net_rewards)
        else:
            variance = 0.25                   #default variance set 

        exploration = np.sqrt(
            (self.alpha * variance * np.log(self.time_step + 1)) / self.T[arm]
        )

        return mean + exploration

    def select_strategy(self):
        """Select strategy with highest UCB"""
        ucb_values = {arm: self.compute_ucb(arm) for arm in range(self.n_arms)}
        return max(ucb_values, key=ucb_values.get)

    def model_call(self, question, temperature=0.0):
        """
        Calls the target model.
        Temperature default = 0 for stable bandit reward estimation.
        """

        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "user", "content": question}
            ],
            options={
                "temperature": temperature,
                "top_p": 0.9,
            }
        )

        return response["message"]["content"]
    
    def model_result(self, question, ground_truth):
        """
        Evaluates whether the model prediction matches ground truth.
        Uses an LLM-as-a-judge to determine if the model was fooled.
        Returns:
            1 if fooled (prediction != ground_truth)
            0 otherwise
        """
        prediction = self.model_call(question)
        
        # Use LLM-as-a-judge to evaluate
        judge_prompt = f"""
        Original ground truth: {ground_truth}
        Model prediction: {prediction}
        
        Determine if the model prediction differs significantly from the ground truth.
        Respond with only 'yes' or 'no'.
        """
        
        judge_response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "user", "content": judge_prompt}
            ],
            options={
                "temperature": 0.0,
                "top_p": 0.9,
            }
        )
        
        judge_verdict = judge_response["message"]["content"].strip().lower()
        fooled = "yes" in judge_verdict
        
        return 1 if fooled else 0


    def attack_sequential(self, input_text, ground_truth, max_rounds=10):
        """
        Apply strategies sequentially until model is fooled or budget exhausted

        Args:
            input_text: Original text
            model: Target model
            ground_truth: original text, unchanged
            max_rounds: Maximum number of strategies to apply

        Returns:
            success: Whether attack succeeded
            perturbed_text: Final perturbed text
            strategies_used: List of strategies applied
        """
        current_text = input_text
        total_cost = 0
        strategies_used = []

        perturbed_indices =[]

        for round_num in range(max_rounds):
            # Check if already fooled
            if self.model_result(current_text, ground_truth) == 1:
                return True, current_text, strategies_used

            # Check budget
            if total_cost >= self.budget:
                break

            self.time_step += 1
            print("round: ", round_num, "\n")
            print("UCB values:", {i: self.compute_ucb(i) for i in range(self.n_arms)}, "\n")
            print("Pull counts:", dict(self.T), "\n")

            # Select next strategy using UCB
            selected_arm = self.select_strategy()

            # Apply the strategy to CURRENT state
            perturbed_text, new_perturbed_indices = self.strategies[selected_arm](current_text, perturbed_indices)

            print("Applied strategy: ", self.strategies[selected_arm].__name__,"\n")
            print("Perturbed text:", perturbed_text, "\n")
            # Calculate cost of THIS perturbation
            num_changed = len(new_perturbed_indices) - len(perturbed_indices)
            cost_this_round = num_changed / len(input_text)  # Relative to original

            perturbed_indices= new_perturbed_indices        #updating perturbed indices for next round
            
            # Check if this would exceed budget
            if total_cost + cost_this_round > self.budget:
                # Try different strategy
                continue

            # Evaluate result
            utility = self.model_result(perturbed_text, ground_truth)

            # Update statistics for THIS strategy
            self.utilities[selected_arm].append(utility)
            self.costs[selected_arm].append(cost_this_round)
            self.T[selected_arm] += 1

            # Accept this perturbation
            current_text = perturbed_text
            total_cost += cost_this_round
            strategies_used.append(selected_arm)

            # Check if fooled
            if utility == 1:
                return True, current_text, strategies_used

        # Attack failed
        final_success = self.model_result(current_text, ground_truth) == 1
        return final_success, current_text, strategies_used




