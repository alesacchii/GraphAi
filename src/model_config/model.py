from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from src.log_config import logger

_RETRY_FEEDBACK = (
    "L'output precedente non rispetta lo schema richiesto.\n"
    "Errore di validazione:\n{error}\n\n"
    "Correggi l'output rispettando esattamente lo schema JSON. "
    "Non aggiungere campi extra e non omettere quelli obbligatori."
)


class AgentConfig:
    """Classe di configurazione e factory per l'agent LangChain.

    Raccoglie in un unico posto i parametri (modello, provider, system prompt,
    tool disponibili) e si occupa di costruire l'agent vero e proprio.
    """

    def __init__(
        self,
        model: str = "gpt-5-nano-2025-08-07",
        provider: str = "openrouter",
    ):
        self.model = model
        self.timeout = 300
        self.provider = provider.rstrip(":")
        logger.info(f"AgentConfig inizializzato (provider={self.provider}, model={self.model})")

    def create_agent(self):
        """Costruisce e restituisce il chat model LangChain pronto all'uso."""
        logger.info("Creazione agent in corso")
        return init_chat_model(
            model=self.model,
            model_provider=self.provider,
        )

    def invoke_structured(
        self,
        schema: type[BaseModel],
        messages: list[BaseMessage],
        max_retries: int = 3,
    ) -> BaseModel:
        """Invoca il modello con structured output e retry su errore di validazione.

        Se il modello produce un output non conforme allo schema Pydantic,
        viene rinvocato fino a `max_retries` volte passandogli la sua risposta
        precedente e l'errore di validazione, in modo che possa correggersi.
        """
        structured = self.create_agent().with_structured_output(
            schema, method="json_schema", include_raw=True
        )

        convo = list(messages)
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            response = structured.invoke(convo)
            parsed = response.get("parsed")
            raw = response.get("raw")
            error = response.get("parsing_error")

            if parsed is not None and error is None:
                return parsed

            last_error = error
            logger.warning(
                f"invoke_structured: tentativo {attempt}/{max_retries} fallito: {error}"
            )
            convo.append(raw)
            convo.append(HumanMessage(content=_RETRY_FEEDBACK.format(error=error)))

        raise RuntimeError(
            f"Structured output fallito dopo {max_retries} tentativi. "
            f"Ultimo errore: {last_error}"
        )