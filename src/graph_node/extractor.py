from src.log_config import logger
from src.graph_config.state import EmailState, FlightData
from src.model_config.model import AgentConfig
from src.util.prompt import extractor_confirmation_prompt, extractor_cancellation_prompt, extractor_schedule_change_prompt
from src.util.base64 import encode_image_to_base64
from src.util.schema import ExtractorSchema
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

def extractor(state: EmailState) -> ExtractorSchema:
    logger.info("[NODE: extractor] Inizio estrazione dati dall'email")
    agent_config = AgentConfig(
        model=os.getenv("OPENROUTER_MODEL_NAME"),
        provider="openrouter",
    )
    logger.info(f"[NODE: extractor] Encoding immagine: {state['image_path']}")
    base64_image = encode_image_to_base64(state["image_path"])

    category = state["document_category"]
    logger.info(f"[NODE: extractor] Selezione prompt per categoria: {category}")
    prompt = ""
    if category == "Confirmation":
        prompt = extractor_confirmation_prompt
    elif category == "Cancellation":
        prompt = extractor_cancellation_prompt
    elif category == "Schedule Change":
        prompt = extractor_schedule_change_prompt

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            }
        ]),
    ]

    logger.info("[NODE: extractor] Invocazione del modello per estrazione strutturata")
    result: ExtractorSchema = agent_config.invoke_structured(ExtractorSchema, messages)
    logger.info(f"[NODE: extractor] Estrazione completata - PNR: {result.pnr}, voli: {len(result.flights)}")
    return {"pnr": result.pnr, "flights": result.flights}
