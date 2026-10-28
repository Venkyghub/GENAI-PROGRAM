
import os

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

env_path = r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
# Load API keys from the .env file
load_dotenv(dotenv_path=env_path, override=False)

# Read API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is missing from the environment.")

if not serper_api_key:
    raise ValueError("SERPER_API_KEY is missing from the environment.")

# Configure the language model
llm = LLM(
    model="openai/gpt-4o-mini",
    api_key=openai_api_key
)

# Researcher is the only agent allowed to search the web
search_tool = SerperDevTool()

researcher = Agent(
    role="Technology News Researcher",
    goal=(
        "Find today's top 3 important technology news stories "
        "using reliable and current web sources."
    ),
    backstory=(
        "You are a technology journalist who researches current "
        "technology developments, verifies dates, and summarizes "
        "important facts with source URLs."
    ),
    tools=[search_tool],
    llm=llm,
    verbose=True
)

# Writer has NO tools, so it cannot search the web
writer = Agent(
    role="Technology Newsletter Writer",
    goal=(
        "Turn the research findings into a concise, accurate "
        "technology newsletter of exactly five lines."
    ),
    backstory=(
        "You are a professional newsletter editor. You use only "
        "the research provided to you and never invent news."
    ),
    tools=[],
    llm=llm,
    verbose=True
)

# Task 1: Research today's top 3 tech stories
research_task = Task(
    description=(
        "Research today's top 3 technology news stories for "
        "October 28, 2026. Use web search to identify current "
        "stories from reliable sources. For each story, provide "
        "a headline, a concise factual summary, the publication "
        "date, and the source URL. Do not present older news "
        "as today's news."
    ),
    expected_output=(
        "Three distinct, verified technology news stories, each "
        "with a headline, factual summary, publication date, "
        "and source URL."
    ),
    agent=researcher
)

# Task 2: Use the Researcher's result as explicit input
newsletter_task = Task(
    description=(
        "Using ONLY the research supplied by the previous task, "
        "write a technology newsletter covering the top 3 stories. "
        "Do not search the web or introduce unsupported facts. "
        "Include concise headlines and useful details. "
        "Format the entire newsletter as exactly 5 lines. "
        "Do not add a greeting, introduction, or conclusion "
        "outside those five lines."
    ),
    expected_output=(
        "Exactly 5 lines of newsletter text, with no extra lines. "
        "Cover all 3 researched stories, preserve factual accuracy, "
        "and include source URLs where practical."
    ),
    agent=writer,
    context=[research_task]
)

# Execute tasks in sequence
news_crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, newsletter_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = news_crew.kickoff()
    print("\n===== FINAL 5-LINE NEWSLETTER =====\n")
    print(result)
