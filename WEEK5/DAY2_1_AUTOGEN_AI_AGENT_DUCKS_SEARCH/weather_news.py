
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from ddgs import DDGS

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


# Load API credentials from your existing .env file
env_path = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        f"OPENAI_API_KEY not found. Check your .env file: {env_path}"
    )


def search_weather_news(city: str) -> str:
    """Search the web for recent weather conditions, forecasts, and weather news for a given city."""
    query = f"latest weather conditions forecast and weather news in {city}"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return f"No search results found for {city}."

        formatted_results = []

        for result in results:
            title = result.get("title", "No title")
            body = result.get("body", "No description")
            url = result.get("href", "")

            formatted_results.append(
                f"Title: {title}\n"
                f"Description: {body}\n"
                f"URL: {url}"
            )

        return "\n\n".join(formatted_results)

    except Exception as exc:
        return f"Weather news search failed: {exc}"


async def main():
    city = input("Enter a city name: ").strip()

    if not city:
        print("Please enter a valid city name.")
        return

    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=api_key,
    )

    try:
        assistant = AssistantAgent(
            name="weather_news_agent",
            model_client=model_client,
            system_message=(
                "You are a Weather News assistant. "
                "Use the search_weather_news tool to find information about "
                "the requested city. Summarize the search results accurately. "
                "Clearly distinguish current conditions from forecasts and "
                "avoid inventing weather measurements. "
                "Your final answer must contain exactly 3 short lines: "
                "line 1: current conditions or the latest reported weather; "
                "line 2: forecast or expected changes; "
                "line 3: important weather news or a useful source note. "
                "If information is unavailable, say so briefly."
            ),
            tools=[search_weather_news],
            reflect_on_tool_use=True,
        )

        result = await assistant.run(
            task=(
                f"Search for recent weather information and weather news "
                f"for {city}. Give me exactly 3 short lines."
            )
        )

        # Print only the final assistant response
        final_message = result.messages[-1].content
        print("\nWeather News:")
        print(final_message)

    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
