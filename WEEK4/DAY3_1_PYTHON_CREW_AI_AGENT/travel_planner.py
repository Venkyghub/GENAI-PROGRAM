
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

# 1. Load OpenAI API key from the .env file
env_path = r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found. Please check your .env file."
    )

# 2. Create the LLM model
llm = LLM(
    model="openai/gpt-4o-mini",
    api_key=api_key,
    temperature=0.7
)

# Get city name from the user
city = input("Enter the city you want to visit: ")

# 3. Create the Travel Planner Agent
travel_planner = Agent(
    role="Travel Planner",
    goal=f"Recommend the best 3 places to visit in {city}.",
    backstory=(
        "You are an experienced travel planner who knows about "
        "tourist attractions, historical landmarks, cultural places, "
        "and popular destinations around the world. You provide "
        "helpful, concise, and interesting travel recommendations."
    ),
    llm=llm,
    verbose=True
)

# 4. Create the Task
travel_task = Task(
    description=(
        f"Suggest exactly 3 places to visit in {city}. "
        "For each place, explain what it is and why visitors "
        "should explore it. Present the answer as a numbered list."
    ),
    expected_output=(
        "A numbered list of exactly 3 places to visit in the city. "
        "Each recommendation must include the place name, a short "
        "description, and a reason to visit."
    ),
    agent=travel_planner
)

# 5. Create the Crew
travel_crew = Crew(
    agents=[travel_planner],
    tasks=[travel_task],
    verbose=True
)

# 6. Execute the Crew and print the result
result = travel_crew.kickoff()

print("\n===== TRAVEL PLANNER RESULTS =====\n")
print(result)
