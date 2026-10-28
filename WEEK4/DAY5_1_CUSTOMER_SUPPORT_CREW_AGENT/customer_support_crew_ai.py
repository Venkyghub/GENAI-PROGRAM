
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai_tools import SerperDevTool

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURATION
# ============================================================

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
FAISS_DIR = APP_DIR / "faiss_index"
TIMEZONE = ZoneInfo("Asia/Kolkata")

# Change this to the actual location of your existing .env file.
ENV_FILE = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

SHEET_HEADERS = [
    "DATETIME",
    "USER ASKED QUERY",
    "REPLY GIVEN BY THE AGENT",
    "SATISFIED(YES/NO)",
]


# ============================================================
# STREAMLIT CONFIGURATION AND NIGHT-SKY DESIGN
# ============================================================

st.set_page_config(
    page_title="Night Sky Customer Support",
    page_icon="🌌",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 12% 16%,
                rgba(255,255,255,.9) 0 1px, transparent 2px),
            radial-gradient(circle at 73% 21%,
                rgba(195,215,255,.9) 0 1px, transparent 2px),
            radial-gradient(circle at 36% 68%,
                rgba(255,255,255,.8) 0 1px, transparent 2px),
            radial-gradient(circle at 88% 78%,
                rgba(205,220,255,.8) 0 1px, transparent 2px),
            linear-gradient(160deg, #17284e, #0b1532 55%, #040713);
        background-size: 170px 170px, 230px 230px,
                         190px 190px, 260px 260px, cover;
        color: #f3f6ff;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(7, 13, 34, .96);
    }

    .hero {
        padding: 24px;
        border: 1px solid rgba(190,210,255,.25);
        border-radius: 18px;
        background: rgba(8,17,43,.88);
        margin-bottom: 20px;
    }

    .hero h1 {
        color: #eef3ff !important;
    }

    .hero p {
        color: #c6d3f4 !important;
    }

    /* Readable sidebar text */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #f3f6ff !important;
    }

    /* Visible buttons with dark text */
    .stButton > button {
        background: #f8fafc !important;
        color: #17213b !important;
        border: 2px solid #a9bad8 !important;
        border-radius: 12px !important;
        min-height: 48px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
    }

    .stButton > button *,
    .stButton > button p,
    .stButton > button span {
        color: #17213b !important;
        -webkit-text-fill-color: #17213b !important;
    }

    .stButton > button:hover {
        background: #dbeafe !important;
        border-color: #38bdf8 !important;
    }

    /* Visible query input */
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #17213b !important;
        -webkit-text-fill-color: #17213b !important;
        caret-color: #17213b !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(17,29,62,.9);
        border: 1px solid rgba(190,210,255,.15);
        border-radius: 14px;
    }

    /* Make text readable in Streamlit input fields */
    .stTextInput input,
    .stTextArea textarea,
    .stChatInput textarea,
    [data-testid="stChatInput"] textarea,
    [data-testid="stTextInput"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
        background-color: rgba(20, 25, 45, 0.95) !important;
    }
    
    /* Make placeholder text visible */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stChatInput textarea::placeholder,
    [data-testid="stChatInput"] textarea::placeholder,
    [data-testid="stTextInput"] input::placeholder {
        color: #C5CAD8 !important;
        -webkit-text-fill-color: #C5CAD8 !important;
        opacity: 1 !important;
    }
    
    /* Keep typed text visible when focused */
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stChatInput textarea:focus {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }    

    /* Fix visibility of user messages and AI responses */
    [data-testid="stChatMessage"],
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }
    
    /* Keep chat cards dark while making text readable */
    [data-testid="stChatMessage"] {
        background-color: rgba(22, 32, 58, 0.96) !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        border-radius: 14px !important;
    }
    
    /* Fix headings and other text inside responses */
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] em {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🌌 Night Sky Customer Support</h1>
        <p>Ask a question, review the answer, and tell us whether it helped.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
ENV_FILE = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

env_override = os.getenv("CUSTOMER_SUPPORT_ENV_FILE")
env_path = Path(env_override).expanduser() if env_override else ENV_FILE

if not env_path.is_file():
    st.error(f"Cannot find your .env file: {env_path}")
    st.stop()

load_dotenv(dotenv_path=env_path, override=True)


required_variables = [
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "GOOGLE_SHEET_ID",
]

missing_variables = [
    key for key in required_variables if not os.getenv(key)
]

if missing_variables:
    st.error(
        "Missing variables in .env: "
        + ", ".join(missing_variables)
    )
    st.stop()


# ============================================================
# FAISS: READ ALL PDF FILES
# ============================================================

def build_faiss_index():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(DATA_DIR.rglob("*.pdf"))

    if not pdf_files:
        return None, f"No PDF files found in {DATA_DIR}"

    documents = []

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(str(pdf_file))

            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""

                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": str(
                                    pdf_file.relative_to(APP_DIR)
                                ),
                                "page": page_number,
                            },
                        )
                    )

        except Exception as exc:
            st.warning(
                f"Could not read {pdf_file.name}: {exc}"
            )

    if not documents:
        return None, "No extractable text was found in the PDFs."

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.environ["OPENAI_API_KEY"],
    )

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(str(FAISS_DIR))

    return (
        vectorstore,
        f"Indexed {len(pdf_files)} PDF file(s), "
        f"{len(chunks)} text chunks.",
    )


# ============================================================
# GOOGLE SHEETS
# ============================================================

def get_google_worksheet():
    credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not credentials_path:
        raise ValueError(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON in your .env file."
        )

    credentials_file = Path(credentials_path).expanduser()

    if not credentials_file.is_absolute():
        credentials_file = (APP_DIR / credentials_file).resolve()

    if not credentials_file.is_file():
        raise FileNotFoundError(
            f"Service-account JSON not found: {credentials_file}"
        )

    credentials = Credentials.from_service_account_file(
        str(credentials_file),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        os.environ["GOOGLE_SHEET_ID"]
    )

    worksheet_name = os.getenv(
        "GOOGLE_SHEET_WORKSHEET", "Support Logs"
    )

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=4,
        )

    existing_headers = worksheet.row_values(1)

    if not existing_headers:
        worksheet.append_row(SHEET_HEADERS)
    elif existing_headers[:4] != SHEET_HEADERS:
        raise ValueError(
            "The first row must contain these headers: "
            + " | ".join(SHEET_HEADERS)
        )

    return worksheet


def append_support_log(query, reply, satisfied):
    worksheet = get_google_worksheet()

    timestamp = datetime.now(TIMEZONE).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )

    worksheet.append_row(
        [
            timestamp,
            query,
            reply,
            "YES" if satisfied else "NO",
        ],
        value_input_option="USER_ENTERED",
    )

    return "Successfully logged the interaction in Google Sheets."


# ============================================================
# INITIALIZE FAISS
# ============================================================

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "faiss_status" not in st.session_state:
    st.session_state.faiss_status = "Not initialized"

if st.session_state.vectorstore is None:
    with st.spinner("Reading PDFs and building the FAISS index..."):
        try:
            store, status = build_faiss_index()
            st.session_state.vectorstore = store
            st.session_state.faiss_status = status
        except Exception as exc:
            st.session_state.faiss_status = (
                f"FAISS initialization failed: {exc}"
            )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending" not in st.session_state:
    st.session_state.pending = None

if "status_message" not in st.session_state:
    st.session_state.status_message = "Ready for your question."


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.subheader("System status")
    st.caption(f"PDF folder: {DATA_DIR}")
    st.caption(f"Environment file: {env_path}")
    st.write(st.session_state.faiss_status)

    if st.button(
        "Build / refresh PDF knowledge base",
        use_container_width=True,
    ):
        with st.spinner("Rebuilding FAISS from all PDFs..."):
            try:
                store, status = build_faiss_index()
                st.session_state.vectorstore = store
                st.session_state.faiss_status = status
            except Exception as exc:
                st.session_state.faiss_status = str(exc)

        st.rerun()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending = None
        st.session_state.status_message = "Ready for your question."
        st.rerun()


# ============================================================
# CREWAI TOOLS
# ============================================================

@tool("Search internal PDF knowledge base")
def search_pdf_knowledge_base(query: str) -> str:
    """Search the FAISS index created from PDFs in the data folder."""
    vectorstore = st.session_state.get("vectorstore")

    if vectorstore is None:
        return (
            "The PDF knowledge base is unavailable. "
            "Check the PDF folder and FAISS initialization."
        )

    matches = vectorstore.similarity_search(query, k=4)

    if not matches:
        return "No relevant PDF passages were found."

    results = []

    for doc in matches:
        results.append(
            f"Source: {doc.metadata.get('source', 'unknown')}, "
            f"page {doc.metadata.get('page', '?')}\n"
            f"{doc.page_content}"
        )

    return "\n\n".join(results)


@tool("Log customer support interaction")
def log_support_interaction(
    query: str,
    reply: str,
    satisfied: str,
) -> str:
    """Log query, final reply, datetime, and YES or NO to Google Sheets."""
    status = satisfied.strip().upper()

    if status not in ("YES", "NO"):
        return "ERROR: satisfaction must be YES or NO."

    try:
        return append_support_log(
            query,
            reply,
            status == "YES",
        )
    except Exception as exc:
        return (
            f"ERROR: Google Sheets logging failed: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# THREE CREWAI AGENTS
# ============================================================

llm = LLM(
    model=os.getenv("CREWAI_MODEL", "openai/gpt-4o-mini"),
    api_key=os.environ["OPENAI_API_KEY"],
)

agent_one = Agent(
    role="First-Line Customer Support Agent",
    goal=(
        "Answer customer questions using the internal PDF documents "
        "indexed in FAISS. Do not invent facts."
    ),
    backstory=(
        "You are a careful support specialist. Search internal documents "
        "and cite filenames or page numbers where possible."
    ),
    tools=[search_pdf_knowledge_base],
    llm=llm,
    verbose=True,
)

agent_two = Agent(
    role="Web Research Support Agent",
    goal=(
        "When the customer is not satisfied with Agent 1, search the web "
        "for the same query and provide a better-supported answer."
    ),
    backstory=(
        "You are a web researcher. Prefer reliable sources and include "
        "source URLs in your answer."
    ),
    tools=[SerperDevTool()],
    llm=llm,
    verbose=True,
)

agent_three = Agent(
    role="Customer Support Logging Agent",
    goal=(
        "Record the original query, final answer, and satisfaction "
        "status in Google Sheets."
    ),
    backstory=(
        "You are a precise record keeper. Call the logging tool once "
        "and report any errors honestly."
    ),
    tools=[log_support_interaction],
    llm=llm,
    verbose=True,
)


# ============================================================
# SEQUENTIAL TASK RUNNERS
# ============================================================

def run_crew_task(agent, task):
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return str(crew.kickoff())



def answer_from_pdfs(query):
    """Retrieve PDF context directly, then ask Agent 1 to answer from it."""

    vectorstore = st.session_state.get("vectorstore")

    if vectorstore is None:
        raise RuntimeError(
            "FAISS knowledge base is unavailable. "
            "Check the PDF folder and FAISS initialization."
        )

    # Retrieve relevant PDF passages directly.
    matches = vectorstore.similarity_search(query, k=5)

    if not matches:
        return (
            "I could not find relevant information in the internal "
            "PDF knowledge base for this question."
        )

    context_parts = []

    for doc in matches:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "unknown")

        context_parts.append(
            f"Source: {source}, page {page}\n"
            f"{doc.page_content}"
        )

    retrieved_context = "\n\n---\n\n".join(context_parts)

    task = Task(
        description=(
            "Answer the customer's question using the retrieved "
            "internal PDF passages provided below.\n\n"
            "RULES:\n"
            "1. Read the retrieved passages before answering.\n"
            "2. Use only facts supported by these passages.\n"
            "3. Cite the source filename and page when available.\n"
            "4. If the passages do not answer part of the question, "
            "clearly say what is missing.\n"
            "5. Never claim that the PDF knowledge base is unavailable "
            "when passages have been supplied below.\n"
            "6. If documents conflict, explain the conflict rather "
            "than silently choosing one version.\n\n"
            f"CUSTOMER QUERY:\n{query}\n\n"
            f"RETRIEVED PDF PASSAGES:\n{retrieved_context}"
        ),
        expected_output=(
            "A clear answer based on the supplied PDF passages, "
            "with source filenames and page numbers where available."
        ),
        agent=agent_one,
    )

    return run_crew_task(agent_one, task)



def answer_from_web(query, first_answer):
    task = Task(
        description=(
            "The customer was not satisfied with the first answer. "
            "Search the web for the SAME original query. Include "
            "reliable source URLs and do not invent facts.\n\n"
            f"ORIGINAL QUERY:\n{query}\n\n"
            f"FIRST ANSWER:\n{first_answer}"
        ),
        expected_output=(
            "A helpful web-researched answer to the original query "
            "with source URLs."
        ),
        agent=agent_two,
    )

    return run_crew_task(agent_two, task)


def run_logging_agent(query, reply, satisfied):
    status = "YES" if satisfied else "NO"

    task = Task(
        description=(
            "Call the Google Sheets logging tool exactly once. "
            "Use the exact query, final reply, and satisfaction value. "
            "Do not rewrite the answer.\n\n"
            f"QUERY:\n{query}\n\n"
            f"FINAL REPLY:\n{reply}\n\n"
            f"SATISFIED: {status}"
        ),
        expected_output=(
            "A confirmation of successful logging or a clear error "
            "message if logging failed."
        ),
        agent=agent_three,
    )

    result = run_crew_task(agent_three, task)

    if "ERROR: Google Sheets logging failed" in result:
        raise RuntimeError(result)

    return result


# ============================================================
# SINGLE-LINE STATUS INDICATOR
# ============================================================

status_placeholder = st.empty()

def show_status(message):
    st.session_state.status_message = message
    status_placeholder.markdown(
        f"""
        <div style="
            background: rgba(8,18,45,.95);
            border: 1px solid #8ba9df;
            border-radius: 10px;
            padding: 12px 16px;
            margin: 10px 0;
            color: #ffffff;
            font-size: 15px;">
            ✨ {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# RECEIVE CUSTOMER QUERY
# ============================================================

if st.session_state.pending is None:
    query = st.chat_input("What can I help you with?")

    if query:
        st.session_state.messages.append(
            {"role": "user", "content": query}
        )

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            show_status("Agent 1 is searching your PDF knowledge base.")

            try:
                with st.spinner("Agent 1 is working..."):
                    first_reply = answer_from_pdfs(query)
            except Exception as exc:
                first_reply = (
                    f"Agent 1 encountered an error: "
                    f"{type(exc).__name__}: {exc}"
                )

            st.markdown(first_reply)

        st.session_state.messages.append(
            {"role": "assistant", "content": first_reply}
        )

        st.session_state.pending = {
            "query": query,
            "first_reply": first_reply,
            "final_reply": first_reply,
            "stage": "feedback",
        }

        st.session_state.status_message = (
            "Agent 1 finished. Waiting for your satisfaction choice."
        )
        st.rerun()


# ============================================================
# SATISFACTION CHOICES
# ============================================================

pending = st.session_state.pending

if pending is not None and pending["stage"] == "feedback":
    show_status(
        "Agent 1 finished. Select Satisfied or Not satisfied."
    )

    st.markdown("### Did this answer solve your problem?")

    col1, col2 = st.columns(2)

    with col1:
        satisfied_clicked = st.button(
            "✅ Satisfied",
            key="satisfied_button",
            use_container_width=True,
        )

    with col2:
        not_satisfied_clicked = st.button(
            "❌ Not satisfied",
            key="not_satisfied_button",
            use_container_width=True,
        )

    if satisfied_clicked:
        show_status(
            "Agent 3 is logging the answer with satisfaction YES."
        )

        try:
            with st.spinner("Agent 3 is writing to Google Sheets..."):
                log_result = run_logging_agent(
                    pending["query"],
                    pending["first_reply"],
                    True,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📋 {log_result}",
                }
            )

            st.session_state.pending = None
            st.session_state.status_message = (
                "Completed. Interaction logged successfully."
            )
            st.success("Thank you! Your feedback has been recorded.")
            st.rerun()

        except Exception as exc:
            show_status("Google Sheets logging failed. Check the error below.")
            st.error(
                f"{type(exc).__name__}: {exc}"
            )

    if not_satisfied_clicked:
        show_status(
            "Agent 2 is searching the web for your original query."
        )

        try:
            with st.spinner("Agent 2 is researching the web..."):
                web_reply = answer_from_web(
                    pending["query"],
                    pending["first_reply"],
                )
        except Exception as exc:
            web_reply = (
                f"Agent 2 encountered an error: "
                f"{type(exc).__name__}: {exc}"
            )

        st.session_state.pending = {
            "query": pending["query"],
            "first_reply": pending["first_reply"],
            "final_reply": web_reply,
            "stage": "log_web",
        }

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "### Web-researched answer\n" + web_reply,
            }
        )

        st.rerun()


# ============================================================
# AGENT 3 AFTER AGENT 2
# ============================================================

pending = st.session_state.pending

if pending is not None and pending["stage"] == "log_web":
    st.markdown("### Web-researched answer")
    st.markdown(pending["final_reply"])

    show_status(
        "Agent 2 finished. Agent 3 is logging the answer with satisfaction NO."
    )

    if st.button(
        "📋 Retry Google Sheets logging",
        key="retry_web_logging",
        use_container_width=True,
    ):
        try:
            with st.spinner("Agent 3 is logging the final web answer..."):
                log_result = run_logging_agent(
                    pending["query"],
                    pending["final_reply"],
                    False,
                )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"📋 {log_result}",
                }
            )

            st.session_state.pending = None
            st.success("Web answer and feedback logged successfully.")
            st.rerun()

        except Exception as exc:
            st.error(
                f"Google Sheets logging failed: "
                f"{type(exc).__name__}: {exc}"
            )

st.caption(
    "Your query and final answer are sent to Google Sheets "
    "when you submit a satisfaction choice."
)
