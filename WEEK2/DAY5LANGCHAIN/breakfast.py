import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load OPENAI_API_KEY from the .env file in the project directory.
env_path = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        f"OPENAI_API_KEY was not found. Check your .env file at: {env_path}"
    )


def main():
    prompt = """
Give exactly 5 healthy breakfast ideas.
For this task, define healthy as a balanced option containing nutrient-dense
ingredients, such as vegetables or fruit, whole grains, and/or a source of protein.
Return only a numbered list from 1 to 5, one idea per line.
Do not include a preamble, explanation, recipe steps, or any text before or after the list.
"""

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=1.0,
    )

    reply = llm.invoke(prompt)

    # invoke() returns a message object; print only the reply text.
    print(reply.content)


if __name__ == "__main__":
    main()
