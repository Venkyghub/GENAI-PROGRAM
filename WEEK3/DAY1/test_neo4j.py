
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Reuse the existing GENAI PROGRAM/.env file
ENV_FILE = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

if not ENV_FILE.is_file():
    raise FileNotFoundError(
        f"Cannot find .env file: {ENV_FILE}"
    )

load_dotenv(ENV_FILE, override=True)

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([URI, USERNAME, PASSWORD]):
    raise ValueError(
        "NEO4J_URI, NEO4J_USERNAME and "
        "NEO4J_PASSWORD must be set in the root .env file."
    )

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

try:
    driver.verify_connectivity()
    print("Neo4j connection successful!")

    with driver.session() as session:
        result = session.run(
            "RETURN 'Connected' AS status"
        )
        print(result.single()["status"])

except Exception as error:
    print("Neo4j connection failed:", error)

finally:
    driver.close()
