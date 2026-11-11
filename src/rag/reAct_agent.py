"""
ReAct agent setup for document retrieval and question answering.

NOTE: this module is intentionally NOT imported at application start-up.
Import `agent_executor` only when you need it; it is not wired into the
main LangGraph pipeline (graph_builder.py uses a dedicated retriever node
instead).
"""

import os

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

from src.config.settings import Config
from src.llms.groq import llm
from src.rag.retriever_setup import search_uploaded_documents

config = Config()

# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------
retriever_tool = StructuredTool.from_function(
    func=search_uploaded_documents,
    name="retriever_customer_uploaded_documents",
    description="Search the user's uploaded documents for passages that answer the question.",
)
tools = [retriever_tool]

# ---------------------------------------------------------------------------
# Load document description produced by document_upload.py (optional)
# We look next to this file so the path is stable regardless of CWD.
# ---------------------------------------------------------------------------
_DESC_PATH = os.path.join(os.path.dirname(__file__), "description.txt")
if os.path.exists(_DESC_PATH):
    with open(_DESC_PATH, "r", encoding="utf-8") as _f:
        _description = _f.read()
else:
    _description = "No document description available."

# ---------------------------------------------------------------------------
# Prompt — create_react_agent requires a *single-string* PromptTemplate
# with the variables: {tools}, {tool_names}, {input}, {agent_scratchpad}.
# Using a ChatPromptTemplate here raises a ValueError.
# ---------------------------------------------------------------------------
_REACT_TEMPLATE = """\
You are a helpful assistant with access to the following tools:

{tools}

To answer the user's question you MUST use this exact format:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation sequence can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Document context:
{description}

Begin!

Question: {{input}}
Thought:{{agent_scratchpad}}""".format(
    tools="{tools}",
    tool_names="{tool_names}",
    description=_description,
)

prompt = PromptTemplate.from_template(_REACT_TEMPLATE)

# ---------------------------------------------------------------------------
# Agent — constructed lazily so import errors surface only when actually used
# ---------------------------------------------------------------------------
def build_agent_executor() -> AgentExecutor:
    react_agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=react_agent,
        tools=tools,
        handle_parsing_errors=True,
        max_iterations=2,
        verbose=True,
        return_intermediate_steps=True,
    )


# Convenience singleton — call build_agent_executor() directly if you need
# a fresh instance (e.g. after uploading a new document).
agent_executor: AgentExecutor | None = None


def get_agent_executor() -> AgentExecutor:
    global agent_executor
    if agent_executor is None:
        agent_executor = build_agent_executor()
    return agent_executor
