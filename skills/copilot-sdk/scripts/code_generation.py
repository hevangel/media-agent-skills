"""
Code Generation Example - GitHub Copilot SDK

This example demonstrates how to use Copilot SDK to generate
Python code based on natural language descriptions.
"""

import asyncio
from pathlib import Path
from copilot import CopilotClient


async def generate_code(session, description: str) -> str:
    """Generate code from a natural language description."""
    prompt = f"""Generate Python code for the following task:

{description}

Requirements:
- Include docstrings and comments
- Follow PEP 8 style guidelines
- Include example usage in if __name__ == "__main__"
- Only output the code, no explanations"""

    print(f"\nGenerating code for: {description}")
    print("-" * 50)

    response = await session.send_and_wait({"prompt": prompt})
    return response.data.content


async def review_code(session, code: str) -> str:
    """Review existing code and suggest improvements."""
    prompt = f"""Review this Python code and suggest improvements:

```python
{code}
```

Focus on:
- Bug fixes
- Performance improvements
- Code readability
- Best practices"""

    print("\nReviewing code...")
    print("-" * 50)

    response = await session.send_and_wait({"prompt": prompt})
    return response.data.content


async def explain_code(session, code: str) -> str:
    """Explain what the code does in plain English."""
    prompt = f"""Explain this Python code in simple terms:

```python
{code}
```

Provide:
1. A brief summary
2. Step-by-step explanation
3. Key concepts used"""

    print("\nExplaining code...")
    print("-" * 50)

    response = await session.send_and_wait({"prompt": prompt})
    return response.data.content


async def add_tests(session, code: str) -> str:
    """Generate unit tests for the given code."""
    prompt = f"""Generate pytest unit tests for this Python code:

```python
{code}
```

Include:
- Test for normal cases
- Test for edge cases
- Test for error handling"""

    print("\nGenerating tests...")
    print("-" * 50)

    response = await session.send_and_wait({"prompt": prompt})
    return response.data.content


async def main():
    """Demonstrate code generation capabilities."""
    print("Starting Copilot client for code generation...")

    client = CopilotClient()
    await client.start()
    print("Client started successfully\n")

    try:
        session = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {
                "mode": "append",
                "content": """You are a Python expert. When generating code:
- Use type hints
- Follow PEP 8
- Write clean, maintainable code
- Include error handling"""
            }
        })
        print("Session created\n")

        # Example 1: Generate a function
        print("=" * 60)
        print("Example 1: Generate a Function")
        print("=" * 60)

        code = await generate_code(
            session,
            "A function that validates email addresses using regex"
        )
        print(f"\n{code}\n")

        # Example 2: Generate a class
        print("=" * 60)
        print("Example 2: Generate a Class")
        print("=" * 60)

        code = await generate_code(
            session,
            "A simple stack data structure class with push, pop, peek, and is_empty methods"
        )
        print(f"\n{code}\n")

        # Example 3: Review some code
        print("=" * 60)
        print("Example 3: Code Review")
        print("=" * 60)

        sample_code = '''
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
'''
        review = await review_code(session, sample_code)
        print(f"\n{review}\n")

        # Example 4: Explain code
        print("=" * 60)
        print("Example 4: Code Explanation")
        print("=" * 60)

        complex_code = '''
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''
        explanation = await explain_code(session, complex_code)
        print(f"\n{explanation}\n")

        # Example 5: Generate tests
        print("=" * 60)
        print("Example 5: Generate Unit Tests")
        print("=" * 60)

        function_code = '''
def is_palindrome(s: str) -> bool:
    """Check if a string is a palindrome."""
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
'''
        tests = await add_tests(session, function_code)
        print(f"\n{tests}\n")

        await session.destroy()
        print("Session destroyed")

    except Exception as e:
        print(f"\nError: {e}")
        raise

    finally:
        await client.stop()
        print("Client stopped")


if __name__ == "__main__":
    asyncio.run(main())
