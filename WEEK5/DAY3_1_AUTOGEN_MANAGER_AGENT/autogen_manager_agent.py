
import os
import asyncio
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ============================================================
# 1. STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Support AI",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. LOAD EXTERNAL .env FILE
# ============================================================

ENV_PATH = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

if ENV_PATH.is_file():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
else:
    load_dotenv(override=False)

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ============================================================
# 3. SUNRISE THEME
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 85% 8%,
                rgba(255, 205, 105, 0.90) 0%,
                rgba(255, 224, 165, 0.35) 13%,
                transparent 28%
            ),
            linear-gradient(
                180deg,
                #A9DDF3 0%,
                #D4EDF9 48%,
                #F5FAFE 100%
            );
        color: #173653;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #173653 !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #B8E2F5 0%, #EAF6FC 100%
        );
        border-right: 1px solid #91C6E1;
    }

    [data-testid="stSidebar"] * {
        color: #173653;
    }

    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #B9D8E9;
        border-radius: 16px;
        color: #173653;
        box-shadow: 0 3px 12px rgba(25, 70, 105, 0.07);
    }

    [data-testid="stChatInput"] {
        background: #FFFFFF;
        border: 2px solid #367FA8;
        border-radius: 14px;
    }

    [data-testid="stChatInput"] textarea {
        color: #173653 !important;
    }

    .stButton > button {
        background: #164D78;
        color: #FFFFFF !important;
        border: 2px solid #164D78;
        border-radius: 10px;
        font-weight: 700;
    }

    .stButton > button:hover {
        background: #0C3557;
        color: #FFFFFF !important;
        border-color: #0C3557;
    }

    [data-testid="stMetricValue"] {
        color: #173653;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "activities" not in st.session_state:
    st.session_state.activities = []

if "last_agent" not in st.session_state:
    st.session_state.last_agent = None

if "request_count" not in st.session_state:
    st.session_state.request_count = 0


# ============================================================
# 5. SPECIALIST AGENT INSTRUCTIONS
# ============================================================

AGENT_INSTRUCTIONS = {

    "IT": """
    You are the IT Support Specialist.

    Handle:
    - Laptop and desktop troubleshooting
    - Wi-Fi and network connectivity
    - Software installation and application errors
    - Printer problems
    - Operating system issues
    - Technical system access problems

    Answer the customer's exact question.
    Give practical, clear, step-by-step troubleshooting.
    Do not introduce unrelated topics.
    Ask a concise clarification question if essential details are missing.
    Do not pretend to know company-specific systems or procedures.
    """,

    "Account": """
    You are the Account Support Specialist.

    Handle:
    - Account login problems
    - Account creation and activation
    - Username and profile issues
    - Account access and recovery
    - Employee account-related questions

    Never ask the user to reveal a password, OTP, recovery code,
    API key, or other secret credential.

    Give clear, practical instructions.
    Ask for clarification if the account problem is unclear.
    """,

    "Security": """
    You are the Security Support Specialist.

    Handle:
    - Phishing emails and suspicious messages
    - Suspicious links and attachments
    - Unauthorized access
    - Password safety
    - Malware concerns
    - Data protection and security incidents

    Prioritize immediate safety.

    For suspected incidents, advise the user to follow their
    organization's official security incident-reporting process.

    Never ask for passwords, OTPs, or secret credentials.
    Do not invent company-specific incident procedures.
    """,

    "Policy": """
    You are the Company Policy Support Specialist.

    Handle internal company and employee policies such as:
    - Annual leave and sick leave
    - Attendance rules
    - Work-from-home policies
    - Employee benefits
    - HR procedures
    - Internal company rules

    Understand the specific policy question before answering.

    If the user says only "employee policy" or asks a very broad
    question, ask which policy they mean.

    Do not invent company-specific policy details or entitlements.

    If official company policy documents are not connected,
    say clearly that the exact rule must be confirmed with HR.

    Do not confuse internal company policy with government policy.
    """
}


# ============================================================
# 6. RESPONSE EXTRACTION
# ============================================================

def extract_response(task_result):
    """Extract the latest non-empty text response from AutoGen."""

    if not getattr(task_result, "messages", None):
        return "The specialist could not generate a response. Please try again."

    for message in reversed(task_result.messages):

        content = getattr(message, "content", None)

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):

            text_parts = []

            for item in content:
                item_text = getattr(item, "text", None)

                if item_text:
                    text_parts.append(item_text)

            if text_parts:
                return "\n".join(text_parts).strip()

    return "The specialist could not generate a response. Please try again."


# ============================================================
# 7. MANAGER ROUTER + FOUR SPECIALIST AGENTS
# ============================================================

async def process_customer_query(user_query, previous_context):

    """
    Manager Agent is ONLY a router.

    It calls one specialist tool for supported queries.
    It never provides customer-facing answers.

    If no specialist is assigned, the application displays
    a standard clarification/out-of-scope message.
    """

    activities = [
        "Manager Agent: Received the customer query.",
        "Manager Agent: Analysing the customer's intent.",
        "Manager Agent: Identifying the correct support team.",
    ]

    assignment = {
        "agent_name": None,
        "specialist_response": None,
        "tool_error": None,
    }

    model_client = None

    try:

        if not API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY was not found. Check the external .env file path."
            )

        # ----------------------------------------------------
        # OPENAI MODEL CLIENT
        # ----------------------------------------------------

        model_client = OpenAIChatCompletionClient(
            model=MODEL_NAME,
            api_key=API_KEY,
        )

        # ----------------------------------------------------
        # CREATE SPECIALIST AGENTS
        # ----------------------------------------------------

        it_agent = AssistantAgent(
            name="IT_Agent",
            model_client=model_client,
            system_message=AGENT_INSTRUCTIONS["IT"],
        )

        account_agent = AssistantAgent(
            name="Account_Agent",
            model_client=model_client,
            system_message=AGENT_INSTRUCTIONS["Account"],
        )

        security_agent = AssistantAgent(
            name="Security_Agent",
            model_client=model_client,
            system_message=AGENT_INSTRUCTIONS["Security"],
        )

        policy_agent = AssistantAgent(
            name="Policy_Agent",
            model_client=model_client,
            system_message=AGENT_INSTRUCTIONS["Policy"],
        )

        # ----------------------------------------------------
        # TOOL 1: IT AGENT
        # ----------------------------------------------------

        async def assign_to_it_agent(query: str) -> str:
            """Delegate technical support queries to the IT Agent."""

            if assignment["agent_name"] is not None:
                return "A specialist has already been assigned."

            assignment["agent_name"] = "IT Agent"

            activities.append(
                "Manager Agent → IT Agent: Assignment successful."
            )

            activities.append(
                "IT Agent: Processing the technical support query."
            )

            try:

                result = await it_agent.run(
                    task=(
                        f"Customer query:\n{query}\n\n"
                        f"Recent conversation:\n{previous_context}\n\n"
                        "Answer the customer's exact question."
                    )
                )

                response = extract_response(result)

                assignment["specialist_response"] = response

                activities.append(
                    "IT Agent: Response generated successfully."
                )

                return response

            except Exception as exc:

                assignment["tool_error"] = str(exc)
                raise

        # ----------------------------------------------------
        # TOOL 2: ACCOUNT AGENT
        # ----------------------------------------------------

        async def assign_to_account_agent(query: str) -> str:
            """Delegate account-related queries to the Account Agent."""

            if assignment["agent_name"] is not None:
                return "A specialist has already been assigned."

            assignment["agent_name"] = "Account Agent"

            activities.append(
                "Manager Agent → Account Agent: Assignment successful."
            )

            activities.append(
                "Account Agent: Processing the account query."
            )

            try:

                result = await account_agent.run(
                    task=(
                        f"Customer query:\n{query}\n\n"
                        f"Recent conversation:\n{previous_context}\n\n"
                        "Answer the customer's exact question."
                    )
                )

                response = extract_response(result)

                assignment["specialist_response"] = response

                activities.append(
                    "Account Agent: Response generated successfully."
                )

                return response

            except Exception as exc:

                assignment["tool_error"] = str(exc)
                raise

        # ----------------------------------------------------
        # TOOL 3: SECURITY AGENT
        # ----------------------------------------------------

        async def assign_to_security_agent(query: str) -> str:
            """Delegate cybersecurity and phishing queries to the Security Agent."""

            if assignment["agent_name"] is not None:
                return "A specialist has already been assigned."

            assignment["agent_name"] = "Security Agent"

            activities.append(
                "Manager Agent → Security Agent: Assignment successful."
            )

            activities.append(
                "Security Agent: Reviewing the security concern."
            )

            try:

                result = await security_agent.run(
                    task=(
                        f"Customer query:\n{query}\n\n"
                        f"Recent conversation:\n{previous_context}\n\n"
                        "Answer the customer's exact question."
                    )
                )

                response = extract_response(result)

                assignment["specialist_response"] = response

                activities.append(
                    "Security Agent: Response generated successfully."
                )

                return response

            except Exception as exc:

                assignment["tool_error"] = str(exc)
                raise

        # ----------------------------------------------------
        # TOOL 4: POLICY AGENT
        # ----------------------------------------------------

        async def assign_to_policy_agent(query: str) -> str:
            """Delegate internal company policy queries to the Policy Agent."""

            if assignment["agent_name"] is not None:
                return "A specialist has already been assigned."

            assignment["agent_name"] = "Policy Agent"

            activities.append(
                "Manager Agent → Policy Agent: Assignment successful."
            )

            activities.append(
                "Policy Agent: Reviewing the company-policy query."
            )

            try:

                result = await policy_agent.run(
                    task=(
                        f"Customer query:\n{query}\n\n"
                        f"Recent conversation:\n{previous_context}\n\n"
                        "Answer the specific company-policy question. "
                        "If it is too broad, ask the customer to clarify."
                    )
                )

                response = extract_response(result)

                assignment["specialist_response"] = response

                activities.append(
                    "Policy Agent: Response generated successfully."
                )

                return response

            except Exception as exc:

                assignment["tool_error"] = str(exc)
                raise

        # ----------------------------------------------------
        # MANAGER AGENT - ROUTING ONLY
        # ----------------------------------------------------

        manager_agent = AssistantAgent(

            name="Manager_Agent",

            model_client=model_client,

            tools=[
                assign_to_it_agent,
                assign_to_account_agent,
                assign_to_security_agent,
                assign_to_policy_agent,
            ],

            system_message="""
            You are the Manager Agent of a Customer Support System.

            YOUR ONLY JOB IS TO ROUTE AND ASSIGN CUSTOMER QUERIES.

            YOU ARE NOT A CUSTOMER-FACING ANSWERING AGENT.

            You must NEVER answer the customer's question yourself.
            You must NEVER provide general knowledge explanations.
            You must NEVER write a customer-facing response.

            AVAILABLE SPECIALISTS AND ROUTING:

            1. IT Agent:
               Laptop, desktop, Wi-Fi, networks, software,
               printers and technical troubleshooting.

            2. Account Agent:
               Login, account creation, activation, profile
               and account-access queries.

            3. Security Agent:
               Phishing, suspicious emails, suspicious links,
               unauthorized access, malware and cybersecurity.

            4. Policy Agent:
               Internal company HR policies, leave, attendance,
               work-from-home rules and employee benefits.

            ROUTING RULES:

            - Understand the customer's actual intent.
            - Do not classify using keywords alone.
            - For a supported query, call exactly ONE matching tool.
            - Pass the original customer query to that specialist.
            - Never call multiple specialist tools.
            - Never answer the customer after the tool returns.
            - The specialist's response is the customer-facing answer.
            - Do not invent or rewrite the specialist's response.

            UNSUPPORTED OR UNCLEAR QUERIES:

            - Do not answer them.
            - Do not call an unrelated specialist.
            - If the query is unclear, do not guess.
            - If no category matches, do not call a tool.
            - The application will display a standard message.

            GOVERNMENT POLICY:

            Government employee rules are not automatically
            internal company policies.

            Do not route them to the Policy Agent unless the user
            is clearly asking about their own company policy.

            Your task ends after assigning the query to one specialist,
            or deciding that no specialist tool is appropriate.
            """,

            reflect_on_tool_use=True,

            max_tool_iterations=2,
        )

        # ----------------------------------------------------
        # RUN MANAGER AGENT
        # ----------------------------------------------------

        activities.append(
            "Manager Agent: Assigning the query to the appropriate specialist."
        )

        await manager_agent.run(
            task=(
                f"CUSTOMER QUERY:\n{user_query}\n\n"
                f"RECENT CONVERSATION:\n{previous_context}\n\n"
                "Your only task is to route this query. "
                "Call exactly one matching specialist tool if the query "
                "belongs to a supported category. Never answer the user."
            )
        )

        # We deliberately do not display the Manager's own message.
        # Only the specialist's response can be displayed.

        if assignment["agent_name"] is not None:

            if assignment["tool_error"]:
                raise RuntimeError(assignment["tool_error"])

            if not assignment["specialist_response"]:
                raise RuntimeError(
                    "The specialist was assigned but did not return a response."
                )

            activities.append(
                "Manager Agent: Assignment completed."
            )

            activities.append(
                "Application: Displaying the specialist response."
            )

            return {
                "success": True,
                "agent": assignment["agent_name"],
                "response": assignment["specialist_response"],
                "activities": activities,
            }

        # ----------------------------------------------------
        # NO SPECIALIST ASSIGNED
        # APPLICATION SUPPLIES STANDARD MESSAGE
        # MANAGER DOES NOT ANSWER
        # ----------------------------------------------------

        activities.append(
            "Manager Agent: No matching specialist was identified."
        )

        activities.append(
            "Application: Requesting the customer to choose a supported category."
        )

        return {
            "success": True,
            "agent": "Support Centre",
            "response": (
                "Thank you for contacting our support centre. "
                "I can help with IT, Account, Security and internal "
                "Company Policy questions. Please provide a question "
                "related to one of these support areas."
            ),
            "activities": activities,
        }

    except Exception as error:

        activities.append(
            f"System Error: {str(error)}"
        )

        return {
            "success": False,
            "agent": "System",
            "response": (
                "Sorry, we encountered an issue while processing your request. "
                "Please try again. If the issue continues, check the terminal "
                "for the technical error."
            ),
            "activities": activities,
        }

    finally:

        if model_client is not None:
            await model_client.close()


# ============================================================
# 8. APPLICATION HEADER
# ============================================================

st.title("🌅 Customer Support AI Assistant")

st.markdown(
    """
    ### Good Morning! How can we help you today?

    Welcome to our AI-powered customer support centre.

    The Manager Agent routes your query to the correct specialist.
    The specialist agent handles the question and provides the answer.
    """
)

st.divider()


# ============================================================
# 9. SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🌞 Support Centre")

    st.write(
        "The Manager Agent routes queries to the appropriate specialist."
    )

    st.divider()

    st.markdown("### 🤖 Available Agents")

    st.markdown(
        """
        🔵 **Manager Agent — Router only**

        🖥️ **IT Agent**

        👤 **Account Agent**

        🛡️ **Security Agent**

        📘 **Policy Agent**
        """
    )

    st.divider()

    st.markdown("### 📊 Session Information")

    st.metric(
        "Queries Submitted",
        st.session_state.request_count
    )

    if st.session_state.last_agent:

        st.markdown("**Last Responding Agent**")

        st.info(st.session_state.last_agent)

    if st.button("🗑️ Clear Chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.activities = []
        st.session_state.last_agent = None
        st.session_state.request_count = 0

        st.rerun()

    st.divider()

    st.caption("Powered by Microsoft AutoGen + OpenAI")


# ============================================================
# 10. CHAT HISTORY
# ============================================================

st.markdown("### 💬 Customer Conversation")

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "assistant" and message.get("agent"):

            st.markdown(
                f"**Responding Agent: {message['agent']}**"
            )

        st.markdown(message["content"])


# ============================================================
# 11. AGENT ACTIVITY MONITOR
# ============================================================

with st.expander(
    "🔍 Agent Activity Monitor",
    expanded=True
):

    if st.session_state.activities:

        for activity in st.session_state.activities:

            if "System Error" in activity:

                st.error(activity)

            elif "Assignment successful" in activity:

                st.success(activity)

            elif "Response generated successfully" in activity:

                st.success(activity)

            elif "Application:" in activity:

                st.info(activity)

            else:

                st.info(activity)

    else:

        st.info(
            "Agent activity will appear here after you submit a query."
        )


# ============================================================
# 12. CUSTOMER INPUT AND PROCESSING
# ============================================================

if not API_KEY:

    st.error(
        "OPENAI_API_KEY was not found. Verify the external .env file path "
        "and confirm it contains OPENAI_API_KEY=..."
    )

    st.caption(f"Configured .env path: {ENV_PATH}")

else:

    user_query = st.chat_input(
        "Type your question here..."
    )

    if user_query:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        st.session_state.request_count += 1

        previous_messages = st.session_state.messages[-7:-1]

        previous_context = "\n".join(
            [
                (
                    "Customer: " if item["role"] == "user"
                    else "Support: "
                ) + item["content"]
                for item in previous_messages
            ]
        )

        with st.spinner(
            "🌤️ Manager Agent is routing your query to the correct specialist..."
        ):

            result = asyncio.run(
                process_customer_query(
                    user_query=user_query,
                    previous_context=previous_context,
                )
            )

        st.session_state.activities = result["activities"]

        st.session_state.last_agent = result["agent"]

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["response"],
                "agent": result["agent"],
            }
        )

        st.rerun()


# ============================================================
# 13. FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#164D78;">
        <b>Customer Support AI</b><br>
        <small>Manager Router | IT | Account | Security | Policy</small>
    </div>
    """,
    unsafe_allow_html=True,
)
