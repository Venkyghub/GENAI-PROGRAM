
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# --------------------------------------------------
# 1. Load environment variables from your existing .env
# --------------------------------------------------
ENV_FILE = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

load_dotenv(ENV_FILE, override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# --------------------------------------------------
# 2. Locate graph_data.json
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
GRAPH_FILE = BASE_DIR / "data" / "graph_data.json"


# --------------------------------------------------
# 3. Store graph nodes and relationships in Neo4j
# --------------------------------------------------
def store_graph():
    if not all([NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD]):
        raise ValueError(
            "Neo4j credentials are missing. Check your .env file."
        )

    if not GRAPH_FILE.is_file():
        raise FileNotFoundError(
            f"Graph data file not found: {GRAPH_FILE}"
        )

    with GRAPH_FILE.open("r", encoding="utf-8") as file:
        graph_data = json.load(file)

    nodes = graph_data["nodes"]
    relationships = graph_data["relationships"]

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    try:
        driver.verify_connectivity()

        with driver.session() as session:

            # Create a uniqueness constraint for node IDs.
            session.run("""
                CREATE CONSTRAINT graph_node_id_unique IF NOT EXISTS
                FOR (n:GraphNode)
                REQUIRE n.id IS UNIQUE
            """).consume()

            # Store nodes.
            for node in nodes:
                label = node["label"]
                name = node["name"]
                node_id = node["id"]
                properties = node.get("properties", {})

                # All nodes receive GraphNode and their specific label.
                query = """
                    MERGE (n:GraphNode {id: $node_id})
                    SET n.name = $name
                    SET n += $properties
                    SET n:ENTITY_LABEL
                    RETURN n.id AS id
                """.replace("ENTITY_LABEL", label)

                session.run(
                    query,
                    node_id=node_id,
                    name=name,
                    properties=properties
                ).consume()

            # Store relationships.
            for rel in relationships:
                source_id = rel["source"]
                target_id = rel["target"]
                rel_type = rel["type"]

                # Relationship types come from our generated JSON.
                # Backticks safely delimit the type identifier.
                query = f"""
                    MATCH (source:GraphNode {{id: $source_id}})
                    MATCH (target:GraphNode {{id: $target_id}})
                    MERGE (source)-[r:`{rel_type}`]->(target)
                    RETURN type(r) AS relationship_type
                """

                session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id
                ).consume()

            # Verify stored graph counts.
            node_count = session.run(
                "MATCH (n:GraphNode) RETURN count(n) AS total"
            ).single()["total"]

            relationship_count = session.run(
                """
                MATCH (:GraphNode)-[r]->(:GraphNode)
                RETURN count(r) AS total
                """
            ).single()["total"]

            print("\nGraph Storage Completed Successfully!")
            print(f"Nodes in input file: {len(nodes)}")
            print(f"Relationships in input file: {len(relationships)}")
            print(f"Nodes stored in Neo4j: {node_count}")
            print(
                "Relationships stored in Neo4j: "
                f"{relationship_count}"
            )

    finally:
        driver.close()


if __name__ == "__main__":
    store_graph()
