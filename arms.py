# all the strategies / arms

# all functions return perturbed_question, indices_perturbed
# ease of generalization and return types
import numpy as np
from collections import defaultdict
import random
import ast

# load all the txt files 
chars_blocks_file = "sorted_most_effective_blocks.txt"    #name of chars_blocks file
random_chars_file = "chars.txt"    # name of random_chars file
math_only_file = "chars.txt"       # name of math symbols homoglyphs file  

def load_blocks():

    """
    File format per line:
        Block Name, start, end, { 'a': ['𝖺', ...], ... }

        unicode_blocks = [ {"name": "alphanumeric", "dict": {'a': ['𝖺', ...], 'b'} } ]
        dictionary within a dictionary for mapping all the homoglyphs per block 

    """
    unicode_blocks = []
  
    with open(chars_blocks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split only first 3 commas
            parts = line.split(",", 3)
            if len(parts) < 4:
                continue

            name = parts[0].strip()
            # start = int(parts[1].strip())
            # end = int(parts[2].strip())
            homoglyph_dict = ast.literal_eval(parts[3].strip())
            unicode_blocks.append({
                "name": name,
                "dict": homoglyph_dict
            })
    return unicode_blocks


def load_chars(file_name = "chars.txt"):

  # loads all possible random homoglyphs in a dict
  # used for reading in any files that just have lists
  # of chars - random_chars or visually similar
  # and math only perturbations


    homoglyph_dict = {}
    with open(file_name, "r", encoding = "utf-8") as homoglyphs_file:
        for line in homoglyphs_file:
            if line.startswith("#"):
                continue
            line = line.strip()
             # maps each char to a list of all available homoglyphs
            homoglyph_dict[line[0]] = [homoglyph for homoglyph in line[1:]]    
    return homoglyph_dict

def load_math_chars(file_name= "chars.txt"):

    math_symbols = ["%", "*", "+", "-", "·", "/", "=", "^", "÷", ">", "<", "{", "}", \
                             "(", ")", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "!"]

    math_dict = {}
    
    
    with open(file_name, "r", encoding="utf-8") as homoglyphs_file:
        for line in homoglyphs_file:
            if line.startswith("#"):      #ignores comments
                continue
            if (line[0] in math_symbols):
                line = line.strip()
                math_dict[line[0]] = [homoglyph for homoglyph in line[1:]]      #adds symbols as a list 
    
    return math_dict
    

# define the similar chars 

most_similar_chars = "chars_two_most_similar.txt"     # file name of visually similar 

similar_dict = load_chars(most_similar_chars)
# use this dict when adding delta
similar_chars = [item for val in similar_dict.values() for item in val]
# now we have a list just with the similar characters that has a global scope

delta = 0.3

#load all the dicts ready for the "arms" to call
whitespaces = [chr(0x2000), chr(0x205F), chr(0x3000)]
unicode_blocks = load_blocks()
homoglyph_dict = load_chars()
math_homoglyph_dict = load_math_chars()


  




def whitespace_perturbation(input_text):
  """
  input_text = original question
  pertubs all possible locations for whitespaces

  """
  
  indices_perturbed = []
  perturbed_question = ""

  for char in input_text:
   for char in input_text:
            # perturb whitespaces
            if char == " " or char == "\t":
                perturbed_question += whitespaces[random.randint(0, 2)]
                indices_perturbed += [input_text.index(char)]
            # char is not whitespace
            else:
                perturbed_question += char

  return perturbed_question, indices_perturbed


def char_block_perturbation(input_text, indices):
    """
        input_text = original question
        indices = list of all positions already pertubed.
    
        perturbs all possible indices in the question with random 
        perturbations
        we could add in a feature where it perturbs only upto 'n' 
        characters in the question, to allow other arms to work on it 

    """

        
    # we use only the best performing top 3 blocks, hence do not need to keep 
    #track of what was used vs what was not 

    perturbed_question = ""
    indices_perturbed= []

    blocks_used = set()

    for ch in input_text:
        if (input_text.index(ch) in indices):
            perturbed_question += ch      
            continue                            #skips the ch if already perturbed

        blocks= unicode_blocks.copy()
        random.shuffle(blocks)

        replaced = False
    for block in blocks:

            homoglyphs = block["dict"].get(ch)
            if homoglyphs:
                perturbed_question += random.choice(homoglyphs)
                indices_perturbed += [input_text.index(ch)]           
                replaced=True
                break                       #breaks the minute it finds a match

            if not replaced:
                perturbed_question += ch      #couldnt find perturbation, so we keep it as is


    return perturbed_question, indices_perturbed

def random_chars_perturbation (input_text, indices):
  """
  input_text = original question
  indices = list of all positions already pertubed.

  randomly perturbing selected random indices in the question using full chars.txt

  """
 
  perturbed_question = ""
  indices_perturbed = []

  for ch in input_text:
    if (input_text.index(ch) in indices):
        perturbed_question += ch      
        continue                            #skips the ch if already perturbed

    # this if condition -> if already perturbed, it can just be added as is
    if ch in homoglyph_dict:
        perturbed_question += random.choice(homoglyph_dict[ch])
        indices_perturbed += [input_text.index(ch)]
    
    else:
        perturbed_question += ch      #add the char (this case if its already perturbed)

  return perturbed_question, indices_perturbed

def math_perturbation (input_text, indices):
  """
  input_text = original question
  indices = list of all positions already pertubed.

  randomly perturbing math symbols

  """
 
  perturbed_question = ""
  indices_perturbed = []

  for ch in input_text:
    if (input_text.index(ch) in indices):
        perturbed_question += ch      
        continue                            #skips the ch if already perturbed

    # this if condition -> if already perturbed, it can just be added as is
    if ch in math_homoglyph_dict:
        perturbed_question += random.choice(math_homoglyph_dict[ch])
        indices_perturbed += [input_text.index(ch)]
    
    else:
        perturbed_question += ch      #add the char (this case if its already perturbed)

  return perturbed_question, indices_perturbed





 
       

       

