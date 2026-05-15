
from src.log_config import logger
from src.graph_config.state import EmailState
from src.model_config.model import AgentConfig
from src.util.prompt import validator_prompt
from src.util.base64 import encode_image_to_base64
from src.util.schema import ValidatorSchema
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import json
import os

load_dotenv()

def validate(state: EmailState) -> dict:
    logger.info("[NODE: validate] Inizio validazione dell'email")
    agent_config = AgentConfig(
        model=os.getenv("OPENROUTER_MODEL_NAME"),
        provider="openrouter",
    )

    logger.info(f"[NODE: validate] Encoding immagine: {state['image_path']}")
    base64_image = encode_image_to_base64(state["image_path"])

    extracted_data = {
        "document_category": state.get("document_category"),
        "pnr": state.get("pnr"),
        "flights": state.get("flights"),
    }

    messages = [
        SystemMessage(content=validator_prompt),
        HumanMessage(content=json.dumps(extracted_data, default=str)),
        HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            }
        ]),
    ]

    logger.info("[NODE: validate] Invocazione del modello per la validazione")
    response: ValidatorSchema = agent_config.invoke_structured(
        ValidatorSchema, messages
    )
    logger.info(f"[NODE: validate] Validazione completata: {response.validator_check}")
    return {"validator_check": response.validator_check}

if __name__ == "__main__":
    print(validate({"image_path": "src/data/email_img/Schedule_Change.png"}))
