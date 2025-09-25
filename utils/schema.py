from typing import Literal
from typing_extensions import Annotated, TypedDict, List, Tuple
from langchain_core.documents import Document

class Search(TypedDict):
    """Search query."""
    query: Annotated[str, ..., "Search query to run."]
    section: Annotated[
        Literal["beginning", "middle", "end"],
        ...,
        "Section to query.",
    ]
 
class State(TypedDict):
    question: str
    query: Search
    context: List[Document]
    answer: str
    chat_history: List[Tuple[str, str]]  # [(role, content), ...]
