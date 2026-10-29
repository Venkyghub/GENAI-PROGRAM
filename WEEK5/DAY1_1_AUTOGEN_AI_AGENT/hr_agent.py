
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


# Load the existing .env file from a different folder
env_path = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)
load_dotenv(dotenv_path=env_path)

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        f"OPENAI_API_KEY was not found. Check your .env file: {env_path}"
    )


async def main():
    # Create the OpenAI model client
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=api_key,
    )

    try:
        # Create the HR assistant agent
        assistant = AssistantAgent(
            name="hr_assistant",
            model_client=model_client,
            system_message="You are an HR assistant.",
        )

        # Ask the agent to write a five-line job description
        await Console(
            assistant.run_stream(
                task="Write a 5-line job description for a Junior Python Developer."
            )
        )

    finally:
        # Close the client to release resources
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
