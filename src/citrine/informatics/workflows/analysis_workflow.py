from typing import List, Optional, Union
from uuid import UUID

from citrine._rest.engine_resource import EngineResourceWithoutStatus
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.workflows.workflow import Workflow
from citrine.gemd_queries.gemd_query import GemdQuery


class LatestBuild(Resource['LatestBuild']):
    """Info on the latest analysis workflow build."""

    status = properties.Optional(properties.String, 'status', serializable=False)
    failures = properties.List(properties.String, 'failure_reason', default=[], serializable=False)
    query = properties.Optional(properties.Object(GemdQuery), 'query', serializable=False)


class AnalysisWorkflow(EngineResourceWithoutStatus['AnalysisWorkflow'], Workflow):
    """An analysis workflow stored on the platform.

    Note that plots are not fully supported. They're captured as raw JSON in order to facilitate
    cloning an existing workflow, but no facilities are provided to validate them in the client.
    """

    uid = properties.UUID('id', serializable=False)
    name = properties.String('data.name')
    description = properties.String('data.description')
    snapshot_id = properties.Optional(properties.UUID, 'data.snapshot_id')
    _plots = properties.List(properties.Raw, 'data.plots', default=[])

    latest_build = properties.Optional(properties.Object(LatestBuild), 'metadata.latest_build',
                                       serializable=False)

    def __init__(self,
                 *,
                 name: str,
                 description: str,
                 snapshot_id: Optional[Union[UUID, str]] = None,
                 plots: List[dict] = []):
        self.name = name
        self.description = description
        self.snapshot_id = snapshot_id
        self._plots = plots

    @property
    def status(self) -> str:
        """An alias for 'latest_build.status', to allow its usage with 'wait_while_validating."""
        return self.latest_build.status

    def _post_dump(self, data: dict) -> dict:
        data["data"]["plots"] = [plot["data"] for plot in data["data"].get("plots") or []]
        return super()._post_dump(data)


class AnalysisWorkflowUpdatePayload(Resource['AnalysisWorkflowUpdatePayload']):
    """An object capturing the analysis workflow upload payload.

    Making this a separate payload makes it explicit that you can only update name and description.
    Additionally, unlike in AnalysisWorkflow, both are optional, to allow changing one without
    changing the other.
    """

    uid = properties.UUID('id', serializable=False)
    name = properties.Optional(properties.String, 'name')
    description = properties.Optional(properties.String, 'description')

    def __init__(self,
                 uid: Union[UUID, str],
                 *,
                 name: Optional[str] = None,
                 description: Optional[str] = None):
        self.uid = uid
        self.name = name
        self.description = description
