"""
Custom Tools Example - GitHub Copilot SDK

This example demonstrates how to define custom tools that
Copilot can call to extend its capabilities.
"""

import asyncio
import random
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool


# Define parameter schemas using Pydantic models
class GetWeatherParams(BaseModel):
    """Parameters for the get_weather tool."""
    city: str = Field(description="The city name to get weather for")


class CalculateParams(BaseModel):
    """Parameters for the calculate tool."""
    expression: str = Field(description="Mathematical expression to evaluate")


class SearchDatabaseParams(BaseModel):
    """Parameters for the search_database tool."""
    query: str = Field(description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")


# Define tools using the @define_tool decorator
@define_tool(description="Get the current weather for a city")
async def get_weather(params: GetWeatherParams) -> str:
    """Simulate fetching weather data."""
    print(f"\n  [Tool called: get_weather({params.city})]")
    
    # Simulate API call with random data
    conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "snowy"]
    temp = random.randint(30, 90)
    condition = random.choice(conditions)
    
    return f"Weather in {params.city}: {temp}°F, {condition}"


@define_tool(description="Calculate a mathematical expression")
def calculate(params: CalculateParams) -> str:
    """Safely evaluate a math expression."""
    print(f"\n  [Tool called: calculate({params.expression})]")
    
    try:
        # Only allow safe math operations
        allowed_chars = set("0123456789+-*/().^ ")
        if not all(c in allowed_chars for c in params.expression):
            return "Error: Invalid characters in expression"
        
        # Replace ^ with ** for Python exponentiation
        expr = params.expression.replace("^", "**")
        result = eval(expr)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@define_tool(description="Search the product database")
async def search_database(params: SearchDatabaseParams) -> str:
    """Simulate database search."""
    print(f"\n  [Tool called: search_database({params.query}, limit={params.limit})]")
    
    # Simulate database results
    await asyncio.sleep(0.1)  # Simulate network delay
    
    products = [
        {"name": "Laptop Pro", "price": 999},
        {"name": "Wireless Mouse", "price": 29},
        {"name": "USB-C Hub", "price": 49},
        {"name": "Monitor 4K", "price": 399},
        {"name": "Keyboard RGB", "price": 89},
    ]
    
    # Simple filter by query
    matches = [p for p in products if params.query.lower() in p["name"].lower()]
    
    if not matches:
        return f"No products found matching '{params.query}'"
    
    return f"Found {len(matches)} products: " + ", ".join(
        f"{p['name']} (${p['price']})" for p in matches[:params.limit]
    )


async def main():
    """Demonstrate custom tools with Copilot."""
    print("Starting Copilot client with custom tools...")
    
    client = CopilotClient()
    await client.start()
    print("Client started successfully\n")

    try:
        # Create session with custom tools
        print("Creating session with tools: get_weather, calculate, search_database")
        session = await client.create_session({
            "model": "gpt-4.1",
            "tools": [get_weather, calculate, search_database]
        })
        print("Session created\n")

        # Test weather tool
        print("=" * 50)
        print("Test 1: Weather Tool")
        print("=" * 50)
        print("Prompt: What's the weather like in Seattle and Tokyo?")
        
        response = await session.send_and_wait({
            "prompt": "What's the weather like in Seattle and Tokyo?"
        })
        print(f"\nResponse: {response.data.content}\n")

        # Test calculate tool
        print("=" * 50)
        print("Test 2: Calculate Tool")
        print("=" * 50)
        print("Prompt: Calculate 15 * 8 + 42 / 6")
        
        response = await session.send_and_wait({
            "prompt": "Calculate 15 * 8 + 42 / 6"
        })
        print(f"\nResponse: {response.data.content}\n")

        # Test database tool
        print("=" * 50)
        print("Test 3: Database Search Tool")
        print("=" * 50)
        print("Prompt: Search for USB products in the database")
        
        response = await session.send_and_wait({
            "prompt": "Search for USB products in the database"
        })
        print(f"\nResponse: {response.data.content}\n")

        # Test combining multiple tools
        print("=" * 50)
        print("Test 4: Multiple Tools")
        print("=" * 50)
        print("Prompt: What's the weather in Paris, and how much is 25% of $399?")
        
        response = await session.send_and_wait({
            "prompt": "What's the weather in Paris, and how much is 25% of $399?"
        })
        print(f"\nResponse: {response.data.content}\n")

        # Clean up
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
