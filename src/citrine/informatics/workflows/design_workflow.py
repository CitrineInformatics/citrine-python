from typing import Optional, Union
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.workflows.workflow import Workflow
from citrine.resources.design_execution import DesignExecutionCollection
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ["DesignWorkflow"]


class DesignWorkflow(Resource["DesignWorkflow"], Workflow, AIResourceMetadata):
    """Object that generates scored materials that may approach higher values of the score.

    Parameters
    ----------
    name: str
        the name of the workflow
    design_space_id: Optional[UUID]
        the UUID corresponding to the design space to use
    predictor_id: Optional[UUID]
        the UUID corresponding to the predictor to use
    predictor_version: Optional[Union[int, str]]
        the version of the predictor to use
    description: Optional[str]
        a description of the workflow

    """

    design_space_id = properties.Optional(properties.UUID, "design_space_id")
    predictor_id = properties.Optional(properties.UUID, "predictor_id")
    predictor_version = properties.Optional(
        properties.Union([properties.Integer, properties.String]), "predictor_version"
    )
    branch_root_id: Optional[UUID] = properties.Optional(
        properties.UUID, "branch_root_id"
    )
    """:Optional[UUID]: Root ID of the branch that contains this workflow."""
    branch_version: Optional[int] = properties.Optional(
        properties.Integer, "branch_version"
    )
    """:Optional[int]: Version number of the branch that contains this workflow."""
    data_source = properties.Optional(properties.Object(DataSource), "data_source")

    status_description = properties.String("status_description", serializable=False)
    """:str: more detailed description of the workflow's status"""
    typ = properties.String("type", default="DesignWorkflow", deserializable=False)

    _branch_id: Optional[UUID] = properties.Optional(
        properties.UUID, "branch_id", serializable=False
    )

    def __init__(
        self,
        name: str,
        *,
        design_space_id: Optional[UUID] = None,
        predictor_id: Optional[UUID] = None,
        predictor_version: Optional[Union[int, str]] = None,
        data_source: Optional[DataSource] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.design_space_id = design_space_id
        self.predictor_id = predictor_id
        self.predictor_version = predictor_version
        self.data_source = data_source
        self.description = description

    def __str__(self):
        return "<DesignWorkflow {!r}>".format(self.name)

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        """Run data modification before building."""
        data_source_id = data.pop("data_source_id", None)
        if data_source_id is not None:
            data["data_source"] = DataSource.from_data_source_id(data_source_id).dump()
        return data

    def _post_dump(self, data: dict) -> dict:
        """Run data modification after dumping."""
        data_source = data.pop("data_source", None)
        if data_source is not None:
            data["data_source_id"] = DataSource.build(data_source).to_data_source_id()
        else:
            data["data_source_id"] = None
        return data

    @property
    def design_executions(self) -> DesignExecutionCollection:
        """Return a resource representing all visible executions of this workflow."""
        if getattr(self, "project_id", None) is None:
            raise AttributeError(
                "Cannot initialize execution without project reference!"
            )
        return DesignExecutionCollection(
            project_id=self.project_id, session=self._session, workflow_id=self.uid
        )

    @property
    def data_source_id(self) -> Optional[str]:
        """A resource referencing the workflow's data source."""
        if self.data_source is None:
            return None
        else:
            return self.data_source.to_data_source_id()

    @data_source_id.setter
    def data_source_id(self, value: Optional[str]):
        if value is None:
            self.data_source = None
        else:
            self.data_source = DataSource.from_data_source_id(value)
