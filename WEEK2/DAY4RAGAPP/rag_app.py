import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv


# Load OPENAI_API_KEY from the .env file in the project directory.
env_path = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Multi-PDF RAG Assistant",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Multi-PDF RAG Assistant")
st.write(
    "Upload multiple PDF documents, ask questions across them, "
    "and check every answer against its source file and page."
)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(
        "OPENAI_API_KEY was not found. Create a .env file beside rag_app.py "
        "and add: OPENAI_API_KEY=your_actual_openai_api_key"
    )
    st.stop()

# Keep the vector store and related information between Streamlit reruns.
if "store" not in st.session_state:
    st.session_state.store = None
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0
if "index_signature" not in st.session_state:
    st.session_state.index_signature = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


with st.sidebar:
    st.header("Indexing settings")
    chunk_size = st.number_input(
        "Chunk size (characters)", min_value=300, max_value=3000,
        value=1000, step=100
    )
    chunk_overlap = st.number_input(
        "Chunk overlap (characters)", min_value=0, max_value=500,
        value=150, step=25
    )
    retrieval_k = st.slider(
        "Relevant chunks to retrieve", min_value=2, max_value=10, value=4
    )
    st.caption("Smaller chunks can improve precise page-level citations.")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.write("**Selected PDFs:**")
    for uploaded_file in uploaded_files:
        st.write(f"• {uploaded_file.name} ({uploaded_file.size:,} bytes)")

    # Use file names and content hashes to detect when the selected documents change.
    import hashlib

    signature_parts = []
    for uploaded_file in uploaded_files:
        content = uploaded_file.getvalue()
        signature_parts.append(
            (uploaded_file.name, hashlib.sha256(content).hexdigest())
        )
    current_signature = tuple(signature_parts)

    if st.button("Build / rebuild knowledge base", type="primary"):
        if chunk_overlap >= chunk_size:
            st.error("Chunk overlap must be smaller than chunk size.")
        else:
            all_pages = []
            progress = st.progress(0, text="Reading PDF documents...")
            try:
                for index, uploaded_file in enumerate(uploaded_files):
                    # PyPDFLoader works with a temporary PDF file.
                    with tempfile.NamedTemporaryFile(
                        suffix=".pdf", delete=False
                    ) as temporary_file:
                        temporary_file.write(uploaded_file.getvalue())
                        temporary_path = temporary_file.name

                    try:
                        pages = PyPDFLoader(temporary_path).load()
                        for page_document in pages:
                            # Keep a friendly filename and convert the PDF page
                            # index (zero-based) to a human-facing page number.
                            page_document.metadata["source"] = uploaded_file.name
                            page_document.metadata["page_number"] = (
                                int(page_document.metadata.get("page", 0)) + 1
                            )
                            all_pages.append(page_document)
                    finally:
                        Path(temporary_path).unlink(missing_ok=True)

                    progress.progress(
                        (index + 1) / len(uploaded_files),
                        text=f"Read {uploaded_file.name}",
                    )

                if not all_pages:
                    st.error("No readable text was found in the uploaded PDFs.")
                else:
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=int(chunk_size),
                        chunk_overlap=int(chunk_overlap),
                        add_start_index=True,
                    )
                    chunks = splitter.split_documents(all_pages)
                    chunks = [
                        document
                        for document in chunks
                        if document.page_content.strip()
                    ]

                    if not chunks:
                        st.error(
                            "No text chunks could be created. "
                            "The PDFs may be scanned images without selectable text."
                        )
                    else:
                        with st.spinner("Creating embeddings and building FAISS index..."):
                            embeddings = OpenAIEmbeddings(api_key=api_key)
                            store = FAISS.from_documents(chunks, embeddings)

                        st.session_state.store = store
                        st.session_state.indexed_files = [
                            uploaded_file.name for uploaded_file in uploaded_files
                        ]
                        st.session_state.chunk_count = len(chunks)
                        st.session_state.index_signature = current_signature
                        st.session_state.chat_history = []
                        st.success(
                            f"Indexed {len(chunks)} chunks from "
                            f"{len(uploaded_files)} PDF file(s)."
                        )
            except Exception as error:
                st.error(f"Could not build the knowledge base: {error}")
            finally:
                progress.empty()

if st.session_state.store is not None:
    st.divider()
    st.subheader("Knowledge base status")
    col1, col2 = st.columns(2)
    col1.metric("Chunks indexed", st.session_state.chunk_count)
    col2.metric("PDF files indexed", len(st.session_state.indexed_files))
    st.caption("Indexed files: " + ", ".join(st.session_state.indexed_files))

    # Warn when the user has selected a different set of files from the indexed set.
    if uploaded_files and st.session_state.index_signature is not None:
        if current_signature != st.session_state.index_signature:
            st.warning(
                "The selected PDFs differ from the indexed knowledge base. "
                "Click **Build / rebuild knowledge base** before asking questions "
                "about the newly selected files."
            )

    st.divider()
    st.subheader("Ask a question")
    question = st.text_input(
        "Question",
        placeholder="Example: What is the leave policy, and which document states it?",
        key="question_input",
    )

    if st.button("Get answer", type="primary") and question.strip():
        try:
            with st.spinner("Searching documents and preparing an answer..."):
                retriever = st.session_state.store.as_retriever(
                    search_kwargs={"k": int(retrieval_k)}
                )
                retrieved_docs = retriever.invoke(question)

                if not retrieved_docs:
                    st.warning("No relevant passages were found in the indexed PDFs.")
                else:
                    context_parts = []
                    for doc in retrieved_docs:
                        filename = doc.metadata.get("source", "Unknown file")
                        page_number = doc.metadata.get(
                            "page_number",
                            int(doc.metadata.get("page", 0)) + 1,
                        )
                        context_parts.append(
                            f"[Source: {filename}, page {page_number}]\n"
                            f"{doc.page_content}"
                        )

                    context = "\n\n---\n\n".join(context_parts)
                    llm = ChatOpenAI(
                        api_key=api_key,
                        model="gpt-4o-mini",
                        temperature=0,
                    )
                    prompt = f"""
You are a careful assistant answering questions from multiple PDF documents.

Rules:
1. Answer using only the supplied document excerpts. Do not invent facts.
2. Cite factual claims using the exact source labels provided, for example
   [Source: handbook.pdf, page 7].
3. If the excerpts do not contain enough information, say that the uploaded
   documents do not provide enough evidence to answer.
4. If sources disagree, explicitly describe the disagreement and cite each
   conflicting source. Do not silently choose one version or pretend the
   documents agree.
5. Distinguish what the documents state from any conclusion you draw.
6. Be clear and concise.

Question:
{question}

Retrieved document excerpts:
{context}
"""
                    response = llm.invoke(prompt)
                    answer_text = (
                        response.content
                        if isinstance(response.content, str)
                        else str(response.content)
                    )
                    st.session_state.chat_history.append(
                        {
                            "question": question,
                            "answer": answer_text,
                            "sources": [
                                {
                                    "source": doc.metadata.get("source", "Unknown file"),
                                    "page": doc.metadata.get(
                                        "page_number",
                                        int(doc.metadata.get("page", 0)) + 1,
                                    ),
                                    "excerpt": doc.page_content,
                                }
                                for doc in retrieved_docs
                            ],
                        }
                    )
        except Exception as error:
            st.error(f"Could not answer the question: {error}")

    # Show previous Q&A results for this indexing session.
    for item in reversed(st.session_state.chat_history):
        st.markdown("### Question")
        st.write(item["question"])
        st.markdown("### Answer")
        st.write(item["answer"])
        st.markdown("**Sources retrieved**")
        seen_sources = set()
        for source in item["sources"]:
            source_key = (source["source"], source["page"])
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                with st.expander(
                    f'{source["source"]} — page {source["page"]}'
                ):
                    st.write(source["excerpt"])
        st.divider()
else:
    st.info("Upload PDFs and build the knowledge base to start asking questions.")

st.caption(
    "Note: PDFs containing only scanned images may need OCR before their text "
    "can be indexed. The API key is loaded from .env and should never be committed "
    "to source control."
)
