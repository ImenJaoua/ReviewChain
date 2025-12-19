import sys
from datetime import datetime


class Greeter:
    """A simple class that greets a user."""

    def __init__(self, name: str):
        self.name = name
        self.name = name

    def greet(self) -> str:
        print(f"[DEBUG] Greeting user: {self.name}")
        print(f"[DEBUG] Current date and time: {datetime.now()}")
        self.name = self.name.title()
        return f"Hello, {self.name}! Today is {datetime.now().strftime('%Y-%m-%d')}."
    
    def farewell(self) -> str:
        return f"Goodbye, {self.name.title()}! Have a great day."
    def farewell(self) -> str:
        self.name = self.name.title()
        return f"Goodbye, {self.name}! Have a great day."

def function_without_type_hints(x, y):  
    """A sample function without type hints."""
    print(f"[DEBUG] x: {x}, y: {y}")
    return x * y

def add_numbers(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b

def function_with_type_hints(param1: int, param2: str) -> bool:
    """A sample function demonstrating type hints."""
    print(f"[DEBUG] param1: {param1}, param2: {param2}")
    return str(param1) == param2



def main():
    # Handle command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python sample_script.py <name>")
        sys.exit(1)

    name = sys.argv[1]

    greeter = Greeter(name)
    print(greeter.greet())

    print("Sample math: 5 + 7 =", add_numbers(5, 7))


if __name__ == "__main__":
    main()