from typing import Literal
from pydantic import BaseModel, Field
from src.graph_config.state import FlightData


class DocumentClassificationSchema(BaseModel):
    """Schema per la classificazione del documento email."""

    document_category: Literal[
        "Confirmation", "Cancellation", "Schedule Change", "Not Useful"
    ] = Field(description="Categoria dell'email")

class ExtractorSchema(BaseModel):
    """Schema per l'estrazione dei dati."""
    pnr: str
    flights: list[FlightData]
    
class ValidatorSchema(BaseModel):
    """Schema per la validazione dei dati."""
    validator_check: bool
    
