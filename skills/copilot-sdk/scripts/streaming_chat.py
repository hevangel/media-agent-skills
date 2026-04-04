"""
Streaming Chat Example - GitHub Copilot SDK

This example demonstrates how to receive streaming responses
from Copilot, showing text as it's generated.
"""

import asyncio
from copilot import CopilotClient


async def main():
    """Streaming chat with Copilot."""
    print("Starting Copilot client...")
    
    client = CopilotClient()
    await client.start()
    print("Client started successfully\n")

    try:
        # Create a session with streaming enabled
        print("Creating streaming session...")
        session = await client.create_session({
            "model": "gpt-4.1",
            "streaming": True
        })
        print("Session created\n")

        # Event to signal when processing is complete
        done = asyncio.Event()

        def on_event(event):
            """Handle streaming events."""
            event_type = event.type.value
            
            if event_type == "assistant.message_delta":
                # Print each chunk as it arrives (no newline)
                delta = event.data.delta_content or ""
                print(delta, end="", flush=True)
            
            elif event_type == "assistant.reasoning_delta":
                # Some models provide reasoning (thinking) content
                delta = event.data.delta_content or ""
                print(f"[Thinking: {delta}]", end="", flush=True)
            
            elif event_type == "assistant.message":
                # Final complete message
                print("\n\n--- Complete ---\n")
            
            elif event_type == "session.idle":
                # Session finished processing
                done.set()
            
            elif event_type == "error":
                print(f"\nError: {event.data}")
                done.set()

        # Subscribe to events
        session.on(on_event)

        # Send a prompt that will generate a longer response
        prompt = "Explain the concept of recursion in programming with a simple example."
        print(f"Prompt: {prompt}\n")
        print("--- Streaming Response ---\n")
        
        await session.send({"prompt": prompt})
        
        # Wait for completion
        await done.wait()

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
