from langgraph.graph import START, StateGraph
from utils.schema import State
from utils.pipeline import analyze_query, retrieve, generate

def build_graph(llm, vector_store, checkpointer=None):
    graph_builder = StateGraph(State)

    graph_builder.add_node("analyze_query", lambda s: analyze_query(s, llm))
    graph_builder.add_node("retrieve", lambda s: retrieve(s, vector_store))
    graph_builder.add_node("generate", lambda s: generate(s, llm))

    graph_builder.add_edge(START, "analyze_query")
    graph_builder.add_edge("analyze_query", "retrieve")
    graph_builder.add_edge("retrieve", "generate")

    return graph_builder.compile(checkpointer=checkpointer)