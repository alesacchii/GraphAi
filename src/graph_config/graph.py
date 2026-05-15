from langgraph.graph import StateGraph, END, START

from src.log_config import logger
from src.graph_node.email_to_image import email_to_image
from src.graph_config.state import EmailState
from src.graph_node.categorize import categorize
from src.graph_node.extractor import extractor
from src.graph_node.validator import validate


def build_graph():
    logger.info("[GRAPH] Costruzione del grafo in corso")
    builder = StateGraph(EmailState)
    builder.add_node("email_to_image", email_to_image)
    builder.add_node("categorize", categorize)
    builder.add_node("extractor", extractor)
    builder.add_node("validator", validate)

    builder.add_edge(START, "email_to_image")
    builder.add_edge("email_to_image", "categorize")
    builder.add_conditional_edges(
        "categorize",
        lambda state: state["document_category"],
        {
            "Confirmation": "extractor",
            "Cancellation": "extractor",
            "Schedule Change": "extractor",
            "Not Useful": END
        }
    )
    builder.add_edge("extractor", "validator")
    builder.add_conditional_edges(
        "validator",
        lambda state: state["validator_check"],
        {
            True: END,
            False: "categorize"
        }
    )

    graph = builder.compile()
    logger.info("[GRAPH] Grafo compilato correttamente")
    png_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_data)
    logger.info("[GRAPH] Diagramma del grafo salvato in graph.png")
    return graph
