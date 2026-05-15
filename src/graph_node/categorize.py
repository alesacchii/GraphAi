from src.log_config import logger
from src.graph_config.state import EmailState
from src.model_config.model import AgentConfig
from src.util.prompt import category_prompt
from src.util.base64 import encode_image_to_base64
from src.util.schema import DocumentClassificationSchema
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

def categorize(state: EmailState) -> dict:
    logger.info("[NODE: categorize] Inizio classificazione dell'email")
    agent_config = AgentConfig(
        model=os.getenv("OPENROUTER_MODEL_NAME"),
        provider="openrouter",
    )

    logger.info(f"[NODE: categorize] Encoding immagine: {state['image_path']}")
    base64_image = encode_image_to_base64(state["image_path"])

    messages = [
        SystemMessage(content=category_prompt),
        HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            }
        ]),
    ]

    logger.info("[NODE: categorize] Invocazione del modello per la classificazione")
    response: DocumentClassificationSchema = agent_config.invoke_structured(
        DocumentClassificationSchema, messages
    )
    logger.info(f"[NODE: categorize] Categoria rilevata: {response.document_category}")
    return {"document_category": response.document_category}

if __name__ == "__main__":
    print(categorize({"image_path": "src/data/email_img/Schedule_Change.png"}))
