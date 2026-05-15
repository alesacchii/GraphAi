import logging
import colorlog

# Nome unico del logger condiviso da tutti i moduli del progetto
LOGGER_NAME = "agenticai"


def _build_logger() -> logging.Logger:
    """Crea (una sola volta) il logger colorato del progetto.

    Usa un flag `_configured` sull'oggetto logger per evitare che chiamate
    multiple aggiungano handler duplicati (cosa che produrrebbe log ripetuti).
    """
    log = logging.getLogger(LOGGER_NAME)

    # Se il logger è già stato configurato in precedenza, lo riutilizziamo
    if getattr(log, "_configured", False):
        return log

    # Handler che stampa su stdout con colori diversi per ogni livello
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s "
            "%(cyan)s%(name)s%(reset)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    # Reset di eventuali handler residui e aggancio del nostro
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    # Disattiva la propagazione al root logger per evitare doppie stampe
    log.propagate = False
    log._configured = True
    return log


# Istanza pronta all'import: `from src.log_config import logger`
logger = _build_logger()
