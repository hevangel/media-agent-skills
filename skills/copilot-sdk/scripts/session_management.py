"""
Session Management Example - GitHub Copilot SDK

This example demonstrates session lifecycle management including
creating, persisting, resuming, and managing multiple sessions.
"""

import asyncio
from copilot import CopilotClient


async def basic_session_lifecycle():
    """Demonstrate basic session creation and cleanup."""
    print("=" * 50)
    print("Basic Session Lifecycle")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        # Create session
        print("Creating session...")
        session = await client.create_session({
            "model": "gpt-4.1"
        })
        print(f"Session created with ID: {session.session_id}")

        # Send a message
        response = await session.send_and_wait({
            "prompt": "Remember this number: 42"
        })
        print(f"Response: {response.data.content[:100]}...")

        # Session maintains context
        response = await session.send_and_wait({
            "prompt": "What number did I ask you to remember?"
        })
        print(f"Response: {response.data.content[:100]}...")

        # Clean up
        await session.destroy()
        print("Session destroyed\n")

    finally:
        await client.stop()


async def persist_and_resume_session():
    """Demonstrate persisting and resuming sessions."""
    print("=" * 50)
    print("Persist and Resume Session")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        # Create first session with custom ID
        session_id = "my-persistent-session"
        print(f"Creating session with ID: {session_id}")

        session = await client.create_session({
            "session_id": session_id,
            "model": "gpt-4.1"
        })

        # Have a conversation
        await session.send_and_wait({
            "prompt": "My favorite color is blue. Remember that."
        })
        print("First message sent")

        # Destroy session (but it persists)
        await session.destroy()
        print("Session destroyed (but persisted)\n")

        # Resume the same session
        print(f"Resuming session: {session_id}")
        resumed_session = await client.resume_session(session_id)

        # Continue conversation
        response = await resumed_session.send_and_wait({
            "prompt": "What's my favorite color?"
        })
        print(f"Response: {response.data.content}")

        # Clean up
        await resumed_session.destroy()
        print("Resumed session destroyed\n")

    finally:
        await client.stop()


async def multiple_concurrent_sessions():
    """Demonstrate managing multiple sessions concurrently."""
    print("=" * 50)
    print("Multiple Concurrent Sessions")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        # Create multiple sessions with different models
        print("Creating 3 sessions...")

        session1 = await client.create_session({
            "model": "gpt-4.1",
            "session_id": "session-gpt"
        })
        session2 = await client.create_session({
            "model": "gpt-4.1",
            "session_id": "session-claude"
        })
        session3 = await client.create_session({
            "model": "gpt-4.1",
            "session_id": "session-general"
        })

        print("Sessions created\n")

        # Send messages to all sessions concurrently
        async def ask_session(session, name, question):
            response = await session.send_and_wait({"prompt": question})
            return f"{name}: {response.data.content[:100]}..."

        # Run concurrently
        results = await asyncio.gather(
            ask_session(session1, "GPT", "What is 2+2?"),
            ask_session(session2, "Claude", "What is 3+3?"),
            ask_session(session3, "General", "What is 4+4?"),
        )

        for result in results:
            print(result)

        print()

        # Clean up all sessions
        await asyncio.gather(
            session1.destroy(),
            session2.destroy(),
            session3.destroy(),
        )
        print("All sessions destroyed\n")

    finally:
        await client.stop()


async def list_and_manage_sessions():
    """Demonstrate listing and managing existing sessions."""
    print("=" * 50)
    print("List and Manage Sessions")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        # Create a few sessions
        sessions = []
        for i in range(3):
            session = await client.create_session({
                "session_id": f"test-session-{i}",
                "model": "gpt-4.1"
            })
            sessions.append(session)
            await session.send_and_wait({"prompt": f"This is session {i}"})

        print(f"Created {len(sessions)} sessions\n")

        # List all sessions
        print("Listing all sessions...")
        session_list = await client.list_sessions()

        for metadata in session_list:
            print(f"  - {metadata.session_id}")

        print()

        # Get message history from a session
        if sessions:
            messages = await sessions[0].get_messages()
            print(f"Session 0 has {len(messages)} messages\n")

        # Clean up
        for session in sessions:
            await session.destroy()
        print("All sessions destroyed\n")

    finally:
        await client.stop()


async def session_with_system_message():
    """Demonstrate sessions with custom system messages."""
    print("=" * 50)
    print("Session with Custom System Message")
    print("=" * 50 + "\n")

    client = CopilotClient()
    await client.start()

    try:
        # Session with appended system message
        print("Creating session with custom personality...")
        session = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {
                "mode": "append",
                "content": """You are a pirate assistant. You:
- Speak like a pirate
- End sentences with 'Arrr!'
- Reference the sea frequently"""
            }
        })

        response = await session.send_and_wait({
            "prompt": "Hello, how are you today?"
        })
        print(f"Pirate response: {response.data.content}\n")

        await session.destroy()

        # Session with replaced system message (full control)
        print("Creating session with replaced system message...")
        session2 = await client.create_session({
            "model": "gpt-4.1",
            "system_message": {
                "mode": "replace",
                "content": "You are a helpful assistant. Always respond in exactly 3 words."
            }
        })

        response = await session2.send_and_wait({
            "prompt": "What is Python?"
        })
        print(f"Three-word response: {response.data.content}\n")

        await session2.destroy()

    finally:
        await client.stop()


async def main():
    """Run all session management examples."""
    await basic_session_lifecycle()
    await persist_and_resume_session()
    await multiple_concurrent_sessions()
    await list_and_manage_sessions()
    await session_with_system_message()

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
