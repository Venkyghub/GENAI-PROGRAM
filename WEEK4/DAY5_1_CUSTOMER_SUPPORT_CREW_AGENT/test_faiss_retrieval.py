
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env",
    override=True,
)

index_path = Path("faiss_index")

try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    print("FAISS index loaded successfully.")

    query = "employee leave policy"
    results = vectorstore.similarity_search_with_score(query, k=5)

    print(f"\nResults returned: {len(results)}")

    for i, (document, score) in enumerate(results, start=1):
        print(f"\n--- Result {i} | Distance: {score:.4f} ---")
        print(document.page_content[:1000])
        print("Metadata:", document.metadata)

except Exception as exc:
    print("ERROR:", type(exc).__name__, repr(exc))
