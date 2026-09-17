"""
Local-mode entrypoint for running the agent interactively from the command line.
"""

import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    from fibey.agent.agent import run_agent

    print("Fibey Agent — Local Mode")
    print("Type 'quit' to exit.\n")

    session: dict = {"history": []}

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        print("Fibey: ", end="", flush=True)
        async for event in run_agent(user_input, session):
            if event["type"] == "delta":
                print(event["content"], end="", flush=True)
            elif event["type"] == "activity":
                status = event.get("status", "")
                tool = event.get("tool", "")
                logger.info("[%s] %s", tool, status)
        print()


if __name__ == "__main__":
    asyncio.run(main())
