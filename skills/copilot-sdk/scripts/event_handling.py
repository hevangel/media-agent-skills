"""
Event Handling Example - GitHub Copilot SDK

This example demonstrates comprehensive event handling
including all event types and proper async patterns.
"""

import asyncio
from copilot import CopilotClient


async def main():
    """Demonstrate comprehensive event handling."""
    print("Starting Copilot client...")

    client = CopilotClient()
    await client.start()
    print("Client started successfully\n")

    try:
        session = await client.create_session({
            "model": "gpt-4.1",
            "streaming": True
        })
        print("Session created\n")

        # Track events for debugging
        event_counts = {}
        done = asyncio.Event()

        def on_event(event):
            """Handle all event types."""
            event_type = event.type.value

            # Count events
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Handle each event type
            if event_type == "assistant.message_delta":
                # Streaming text chunk
                delta = event.data.delta_content or ""
                print(delta, end="", flush=True)

            elif event_type == "assistant.message":
                # Final complete message
                print("\n\n[Complete message received]")
                print(f"Total tokens: {getattr(event.data, 'total_tokens', 'N/A')}")

            elif event_type == "assistant.reasoning_delta":
                # Streaming reasoning/thinking
                delta = event.data.delta_content or ""
                print(f"[Thinking: {delta}]", end="", flush=True)

            elif event_type == "assistant.reasoning":
                # Complete reasoning
                print("\n[Reasoning complete]")

            elif event_type == "tool.call":
                # Tool is being called
                tool_name = getattr(event.data, 'name', 'unknown')
                print(f"\n[Calling tool: {tool_name}]")

            elif event_type == "tool.result":
                # Tool returned result
                print("[Tool completed]")

            elif event_type == "session.idle":
                # Session finished all processing
                print("\n[Session idle]")
                done.set()

            elif event_type == "error":
                # Error occurred
                print(f"\n[Error: {event.data}]")
                done.set()

            else:
                # Unknown/new event type
                print(f"\n[Unknown event: {event_type}]")

        # Subscribe to all events
        unsubscribe = session.on(on_event)

        # Send a prompt
        print("Prompt: Write a haiku about programming\n")
        print("--- Response ---\n")

        await session.send({"prompt": "Write a haiku about programming"})

        # Wait for completion with timeout
        try:
            await asyncio.wait_for(done.wait(), timeout=30)
        except asyncio.TimeoutError:
            print("\n[Timeout waiting for response]")

        # Print event statistics
        print("\n--- Event Statistics ---")
        for event_type, count in sorted(event_counts.items()):
            print(f"  {event_type}: {count}")

        # Unsubscribe from events (optional, session.destroy does this too)
        if unsubscribe:
            unsubscribe()

        await session.destroy()
        print("\nSession destroyed")

    except Exception as e:
        print(f"\nError: {e}")
        raise

    finally:
        await client.stop()
        print("Client stopped")


async def multiple_handlers_example():
    """Demonstrate using multiple event handlers."""
    print("\n" + "=" * 50)
    print("Multiple Handlers Example")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session({"model": "gpt-4.1"})
        done = asyncio.Event()

        # Handler 1: Log all events
        def logger(event):
            print(f"[LOG] Event: {event.type.value}")

        # Handler 2: Collect messages
        messages = []

        def collector(event):
            if event.type.value == "assistant.message":
                messages.append(event.data.content)
            elif event.type.value == "session.idle":
                done.set()

        # Subscribe both handlers
        unsub1 = session.on(logger)
        unsub2 = session.on(collector)

        await session.send({"prompt": "Say 'Hello!'"})
        await done.wait()

        print(f"\nCollected {len(messages)} message(s):")
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. {msg[:50]}...")

        await session.destroy()

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(multiple_handlers_example())
