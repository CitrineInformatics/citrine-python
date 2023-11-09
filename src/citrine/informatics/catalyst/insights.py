from typing import Optional

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine.informatics.catalyst.language_model import LanguageModelChoice


class InsightsRequest(Serializable["InsightsRequest"]):
    """A query to the model insights."""

    question = properties.String("question")
    temperature = properties.Optional(properties.Float, "temperature", default=0.0)
    language_model = properties.Optional(
        properties.Enumeration(LanguageModelChoice),
        "language_model",
        default=LanguageModelChoice.GPT_35_TURBO,
    )
    n_documents = properties.Optional(properties.Integer, "n_documents", default=5)
    response_size = properties.Optional(properties.Integer, "response_size", default=100)

    def __init__(
        self,
        *,
        question: str,
        temperature: Optional[float] = 0.0,
        language_model: Optional[LanguageModelChoice] = LanguageModelChoice.GPT_35_TURBO,
        n_documents: Optional[int] = 5,
        response_size: Optional[int] = 100,
    ):
        self.question = question
        self.temperature = temperature
        self.language_model = language_model
        self.n_documents = n_documents
        self.response_size = response_size


class InsightsResponse(Serializable["InsightsResponse"]):
    """A response from the model insights."""

    response = properties.String("response")
    relevant_documents = properties.Boolean("relevant_documents")
    document_metadata = properties.List(
        properties.Mapping(properties.String, properties.String), "document_metadata"
    )
