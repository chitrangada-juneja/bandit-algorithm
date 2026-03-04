from SequentialUCB import SequentialUCB
from arms import (
    whitespace_perturbation,
    char_block_perturbation,
    random_chars_perturbation,
    math_perturbation
)

arms_list = [
    whitespace_perturbation,
    char_block_perturbation,
    random_chars_perturbation,
    math_perturbation
]

bandit = SequentialUCB(strategies=arms_list, budget=1.0)

success, final_text, used = bandit.attack_sequential(
    input_text="What is 2 + 2?",
    ground_truth="What is 2 + 2?"
)

print(success)
