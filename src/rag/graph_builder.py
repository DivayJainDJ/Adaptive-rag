"""
Graph builder module for the adaptive RAG system.
"""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.constants import START, END
from langgraph.graph.state import StateGraph

from src.rag.retriever_setup import get_base_retriever, search_uploaded_documents
from src.config.settings import Config
from src.llms.groq import llm
from src.models.grade import Grade
from src.models.route_identifier import RouteIdentifier
from src.models.state import State
from src.tools.graph_tools import routing_tool, doc_tool

config = Config()


def _docs_to_text(docs) -> str:
    if not docs:
        return ""
    if isinstance(docs, str):
        return docs
    parts = []
    for doc in docs:
        content = getattr(doc, "page_content", None)
        parts.append(content if content is not None else str(doc))
    return "\n\n".join(parts)


def _latest_question(state: State) -> str:
    if state.get("latest_query"):
        return state["latest_query"]
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content
        content = getattr(message, "content", None)
        if content:
            return content
    return ""


def query_classifier(state: State):
    question = _latest_question(state)
    retriever = get_base_retriever()
    if retriever is None:
        context = "No documents have been uploaded yet."
    else:
        try:
            docs = retriever.invoke(question)
            context = _docs_to_text(docs) or "No relevant documents found."
        except Exception as exc:
            print(f"retriever failed during classification: {exc}")
            context = ""

    llm_with_structured_output = llm.with_structured_output(RouteIdentifier, method="json_mode")
    classify_prompt = PromptTemplate(
        template=config.prompt("classify_prompt"),
        input_variables=["question", "context"],
    )
    chain = classify_prompt | llm_with_structured_output
    result = None
    # Groq's json_mode occasionally returns an unparseable generation; one
    # retry keeps a single bad completion from failing the whole request.
    for attempt in range(2):
        try:
            result = chain.invoke({"question": question, "context": context})
            break
        except Exception as exc:  # noqa: BLE001 - any provider/parse error is retryable
            print(f"classification attempt {attempt + 1} failed: {exc}")
    route = (getattr(result, "route", None) or "general").strip().lower()
    if route not in {"index", "general", "search"}:
        route = "general"
    print(f"query classified as {route}")
    return {"messages": state["messages"], "route": route, "latest_query": question}


def general_llm(state: State):
    result = llm.invoke(state["messages"])
    # `add_messages` reducer expects a list; always wrap the single AIMessage.
    return {"messages": [result]}


def retriever_node(state: State):
    query = _latest_question(state)
    content = search_uploaded_documents(query)
    return {
        "messages": [
            AIMessage(
                content=content,
                additional_kwargs={
                    "tool_calls": [{"tool": "search_uploaded_documents", "input": query}]
                },
            )
        ],
        "latest_query": query,
        "route": state.get("route") or "index",
    }


def grade(state: State):
    grading_prompt = PromptTemplate(
        template=config.prompt("grading_prompt"),
        input_variables=["question", "context"],
    )
    context = state["messages"][-1].content
    question = _latest_question(state)
    grade_chain = grading_prompt | llm.with_structured_output(Grade, method="json_mode")
    result = None
    for attempt in range(2):
        try:
            result = grade_chain.invoke({"question": question, "context": context})
            break
        except Exception as exc:  # noqa: BLE001 - any provider/parse error is retryable
            print(f"grading attempt {attempt + 1} failed: {exc}")
    score = (getattr(result, "binary_score", None) or "no").strip().lower()
    if score not in {"yes", "no"}:
        score = "yes" if "yes" in score else "no"
    return {"messages": state["messages"], "binary_score": score}


def rewrite_query(state: State):
    query = _latest_question(state)
    rewrite_prompt = PromptTemplate(
        template=config.prompt("rewrite_prompt"),
        input_variables=["query"],
    )
    result = (rewrite_prompt | llm).invoke({"query": query})
    # Strip any leading/trailing whitespace and quotes the LLM may add.
    rewritten = result.content.strip().strip('"').strip("'").strip()
    # Fallback to original if the model returned something suspiciously long
    if len(rewritten) > 500 or not rewritten:
        rewritten = query
    return {
        "latest_query": rewritten,
        "rewrite_count": (state.get("rewrite_count") or 0) + 1,
    }


def generate(state: State):
    context = state["messages"][-1].content
    question = _latest_question(state)
    generate_prompt = PromptTemplate(
        template=config.prompt("generate_prompt"),
        input_variables=["context", "question"],
    )
    result = (generate_prompt | llm).invoke({"context": context, "question": question})
    return {"messages": [AIMessage(content=result.content)]}


def web_search(state: State):
    query = _latest_question(state)
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        result = TavilySearchResults(max_results=5).invoke(query)
        if isinstance(result, str):
            contents = result
        else:
            contents = "\n\n".join(
                item.get("content", str(item)) if isinstance(item, dict) else str(item)
                for item in result
            )
        if not str(contents).strip():
            contents = "No web results were returned."
    except Exception as exc:
        contents = (
            f"Web search is unavailable ({exc}). Answer using general knowledge instead."
        )
    return {"messages": [AIMessage(content=contents)]}


def compile_graph(force_route: str | None = None):
    graph = StateGraph(State)
    graph.add_node("query_analysis", query_classifier)
    graph.add_node("retriever", retriever_node)
    graph.add_node("grade", grade)
    graph.add_node("generate", generate)
    graph.add_node("rewrite", rewrite_query)
    graph.add_node("web_search", web_search)
    graph.add_node("general_llm", general_llm)

    if force_route == "index":
        graph.add_edge(START, "retriever")
    else:
        graph.add_edge(START, "query_analysis")
        graph.add_conditional_edges("query_analysis", routing_tool)

    graph.add_edge("web_search", "generate")
    graph.add_edge("retriever", "grade")
    graph.add_edge("rewrite", "retriever")
    graph.add_conditional_edges("grade", doc_tool)
    graph.add_edge("generate", END)
    graph.add_edge("general_llm", END)
    return graph.compile()


builder = compile_graph()
unrouted_builder = compile_graph(force_route="index")
