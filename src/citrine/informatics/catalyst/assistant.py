from typing import Optional, Type

from citrine.informatics.predictors import GraphPredictor
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.catalyst.language_model import LanguageModelChoice


class AssistantRequest(Serializable["AssistantRequest"]):
    """A query to the model assistant."""

    question = properties.String("question")
    predictor = properties.Object(GraphPredictor, "config")
    temperature = properties.Optional(properties.Float, "temperature", default=0.0)
    language_model = properties.Optional(properties.Enumeration(LanguageModelChoice),
                                         "language_model", default=LanguageModelChoice.GPT_4)

    def __init__(self, *,
                 question: str,
                 predictor: GraphPredictor,
                 temperature: Optional[float] = 0.0,
                 language_model: Optional[LanguageModelChoice] = LanguageModelChoice.GPT_4):
        self.question = question
        self.predictor = predictor
        self.temperature = temperature
        self.language_model = language_model

    def _post_dump(self, data: dict) -> dict:
        # When dumping, GraphPredictor.dump isn't called, resulting in some fields being dropped.
        data["config"] = self.predictor.dump()["instance"]
        return super()._post_dump(data)


class AssistantResponse(PolymorphicSerializable["AssistantResponse"]):
    """The parent type for all Model Assistant responses."""

    @classmethod
    def get_type(cls, data) -> Type['AssistantResponse']:
        """Return the subtype."""
        type_dict = {
            "message": AssistantResponseMessage,
            "modified-config": AssistantResponseConfig,
            "unsupported": AssistantResponseUnsupported,
            "input-error": AssistantResponseInputErrors,
            "exec-error": AssistantResponseExecError
        }
        typ = type_dict.get(data['type'])
        if typ is not None:
            return typ
        else:
            raise ValueError(
                f'{data["type"]} is not a valid assistant response type. '
                f'Must be in {type_dict.keys()}.'
            )


class AssistantResponseMessage(Serializable["AssistantResponseMessage"], AssistantResponse):
    """A successful model assistant invocation, whose response is only text."""

    message = properties.String("data.message")


class AssistantResponseConfig(Serializable["AssistantResponseConfig"], AssistantResponse):
    """A successful model assistant invocation, whose response includes a modified predictor."""

    predictor = properties.Object(GraphPredictor, "data.config")

    @classmethod
    def _pre_build(cls, data):
        data["data"]["config"] = GraphPredictor.wrap_instance(data["data"]["config"])
        return data


class AssistantResponseUnsupported(Serializable["AssistantResponseUnsupported"],
                                   AssistantResponse):
    """A successful model assistant invocation, but for an unsupported query.

    This will cover any user query which the model assistant could not map to a functionality it
    supports. For example, asking a generic question, or something unrelated to materials.
    """

    message = properties.String("data.message")


class AssistantResponseInputError(Serializable["AssistantResponseInputError"], AssistantResponse):
    """A single input failure.

    Contains the error message, and the field it applies to.
    """

    field = properties.Optional(properties.String, "field")
    error = properties.String("error")


class AssistantResponseInputErrors(Serializable["AssistantResponseInputErrors"],
                                   AssistantResponse):
    """A failed model assistant invocation, due to malformed input.

    This should only happen if there's some field omitted by the client, or one of its values is
    outside acceptable ranges.
    """

    errors = properties.List(properties.Object(AssistantResponseInputError), "data.errors")


class AssistantResponseExecError(Serializable["AssistantResponseExecError"], AssistantResponse):
    """A failed model assistant invocation, due to some internal issue.

    This most likely indicates the assistant got some unexpected output when asking its query. It
    indicates an internal error, not a problem with the client invocation.
    """

    error = properties.String("data.error")
