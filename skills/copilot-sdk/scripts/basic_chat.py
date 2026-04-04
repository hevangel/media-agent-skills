"""
Basic Chat Example - GitHub Copilot SDK

This example demonstrates the simplest way to use the Copilot SDK
to send a message and receive a response.
"""

import asyncio
from copilot import CopilotClient


async def main():
    """Simple chat with Copilot using send_and_wait."""
    print("Starting Copilot client...")
    
    # Create and start the client
    client = CopilotClient()
    await client.start()
    print("Client started successfully")

    try:
        # Create a session with a specific model
        print("Creating session...")
        session = await client.create_session({"model": "gpt-4.1"})
        print("Session created")

        # Send a message and wait for the complete response
        print("\nSending prompt: 'What is Python?'")
        response = await session.send_and_wait({
            "prompt": "What is Python? Answer in 2-3 sentences."
        })

        # Print the response
        print("\n--- Response ---")
        print(response.data.content)
        print("----------------\n")

        # Demonstrate multi-turn conversation
        print("Sending follow-up: 'What are its main uses?'")
        response = await session.send_and_wait({
            "prompt": "What are its main uses?"
        })

        print("\n--- Response ---")
        print(response.data.content)
        print("----------------\n")

        # Clean up session
        await session.destroy()
        print("Session destroyed")

    except Exception as e:
        print(f"Error: {e}")
        raise

    finally:
        # Always stop the client
        await client.stop()
        print("Client stopped")


if __name__ == "__main__":
    asyncio.run(main())
