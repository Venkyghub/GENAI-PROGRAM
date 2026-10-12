
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load your existing .env file
ENV_FILE = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)
load_dotenv(ENV_FILE, override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def run_queries():
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    try:
        driver.verify_connectivity()

        with driver.session() as session:

            # Query 1: Count all stored schemes
            result = session.run("""
                MATCH (s:GraphNode:Scheme)
                RETURN count(s) AS total_schemes
            """)
            print("\n1. TOTAL SCHEMES")
            print("----------------")
            print(result.single()["total_schemes"])

            # Query 2: List scheme names and departments
            result = session.run("""
                MATCH (s:GraphNode:Scheme)
                OPTIONAL MATCH (s)-[:BELONGS_TO]->(d:GraphNode:Department)
                RETURN s.name AS scheme,
                       d.name AS department
                ORDER BY scheme
                LIMIT 10
            """)
            print("\n2. SCHEMES AND THEIR DEPARTMENTS")
            print("--------------------------------")
            for record in result:
                print(
                    f"Scheme: {record['scheme']} | "
                    f"Department: {record['department'] or 'Not available'}"
                )

            # Query 3: Find schemes for a particular beneficiary
            beneficiary = "Farmers"

            result = session.run("""
                MATCH (s:GraphNode:Scheme)
                      -[:HAS_BENEFICIARY]->
                      (b:GraphNode:Beneficiary)
                WHERE toLower(b.name) CONTAINS toLower($beneficiary)
                RETURN s.name AS scheme, b.name AS beneficiary
                ORDER BY scheme
            """, beneficiary=beneficiary)

            print(f"\n3. SCHEMES FOR: {beneficiary.upper()}")
            print("--------------------------------")
            records = list(result)
            if records:
                for record in records:
                    print(
                        f"Scheme: {record['scheme']} | "
                        f"Beneficiary: {record['beneficiary']}"
                    )
            else:
                print("No matching schemes found.")

    finally:
        driver.close()


if __name__ == "__main__":
    run_queries()
