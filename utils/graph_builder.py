from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition
from utils.nodes import query_or_respond, tools, generate

def build_graph():
    graph_builder = StateGraph(MessagesState)
    
    graph_builder.add_node("query_or_respond", query_or_respond)
    graph_builder.add_node("tools", tools)
    graph_builder.add_node("generate", generate)

    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    return graph_builder   # return builder, not compiled graph

