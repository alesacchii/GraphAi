from src.log_config import logger
from src.graph_config.graph import build_graph

if __name__ == "__main__":
    logger.info("Avvio applicazione AgenticAI")
    graph = build_graph()
    file_path = "src/data/email/New_Volo2.eml"
    logger.info(f"Invocazione del grafo sul file: {file_path}")
    result = graph.invoke({"file_path": file_path})
    logger.info(f"Esecuzione completata. Risultato finale: {result}")
