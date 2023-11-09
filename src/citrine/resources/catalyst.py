from citrine.informatics.catalyst.insights import InsightsResponse, InsightsRequest
from citrine.informatics.catalyst.assistant import AssistantResponse, AssistantRequest
from citrine.informatics.predictors.graph_predictor import GraphPredictor
from citrine.resources.user import UserCollection
from citrine._session import Session
from citrine._utils.functions import resource_path


class CatalystResource:
    """Encapsulates th ability to invoke Catalyst."""

    _path_template: str = '/catalyst'
    _api_version = 'v1'

    def __init__(self, session: Session):
        self.session: Session = session

    def _get_path(self, action: str):
        """Construct a Catalyst url from a base path and action."""
        return resource_path(path_template=self._path_template, action=action)

    def _ensure_internal_user(self):
        """Ensure that the user is internal; raise an error otherwise."""
        user = UserCollection(self.session).me()
        if not user.is_internal:
            raise NotImplementedError(
                "I'm sorry, but this feature is not currently available for "
                "your organization. Please watch the release notes for "
                "updates."
            )

    def assistant(self, query: str, *, predictor: GraphPredictor) -> AssistantResponse:
        """Invoke the model assistant.

        Parameters
        ----------
        query: str
            The query or instruction to pass to the assistant
        predictor: GraphPredictor
            The predictor you wish for the assistant to consider or act on in your query

        Returns
        -------
        The assistant response, containing details of the result of your query which vary by type.

        """
        self._ensure_internal_user()

        payload = AssistantRequest(question=query, predictor=predictor).dump()
        path = self._get_path("assistant")
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return AssistantResponse.build(data)

    def insights(self, query: str) -> InsightsResponse:
        """Invoke the insights.

        Parameters
        ----------
        query: str
            The query or instruction to pass to the insights

        Returns
        -------
        The insights response, containing details of the result of your query which vary by type.

        """
        self._ensure_internal_user()

        payload = InsightsRequest(question=query).dump()
        path = self._get_path(["documents", "search"])
        data = self.session.post_resource(path, json=payload, version=self._api_version)
        return InsightsResponse.build(data)
