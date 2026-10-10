
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI


def main():
    llm = ChatOpenAI(model="gpt-4o-mini")

    prompts = [
        "Explain LangChain in simple terms in 3 sentences.",
        "Give three practical uses of generative AI in digital marketing.",
        (
            "Explain how a RAG system works, including document retrieval, "
            "context injection, and answer generation. Give a practical example."
        ),
    ]

    for index, prompt in enumerate(prompts, start=1):
        print("\n" + "=" * 60)
        print(f"RUN {index}")
        print("=" * 60)
        print(f"PROMPT: {prompt}")

        response = llm.invoke(prompt)
        print("\nANSWER:")
        print(response.content)

    print("\nAll three prompts processed successfully.")


if __name__ == "__main__":
    main()
