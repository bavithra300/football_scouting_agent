
import sys
import os
from unittest.mock import patch

# Ensure the current directory is in path to import football_system
sys.path.append(os.getcwd())

import football_system

# Inputs to feed to the system
inputs = [
    "player",          # Choice
    "Forward",         # Position
    "20-25",           # Age
    "3+ years",        # Experience
    "Attacking, fast"  # Style
]

def mock_input(prompt=""):
    print(f"[MOCK INPUT] Prompt: {prompt}")
    if not inputs:
        raise EOFError("No more inputs available for mock.")
    val = inputs.pop(0)
    print(f"[MOCK INPUT] Entering: {val}")
    return val

def run_test():
    print("Starting Verification Test...")
    with patch('builtins.input', side_effect=mock_input):
        football_system.main()
    print("Verification Test Completed Successfully.")

if __name__ == "__main__":
    run_test()
