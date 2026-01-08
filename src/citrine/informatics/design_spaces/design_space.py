"""Tools for working with design spaces."""

from typing import Optional, Type
from uuid import UUID

from citrine._rest.asynchronous_object import AsynchronousObject
from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.resources.sample_design_space_execution import (
    SampleDesignSpaceExecutionCollection,
)


__all__ = ["DesignSpace"]


class DesignSpace(PolymorphicSerializable["DesignSpace"], AsynchronousObject):
    """A Citrine Design Space describes the set of materials that can be made.

    Abstract type that returns the proper type given a serialized dict.

    """

    uid = properties.Optional(properties.UUID, "id", serializable=False)
    """:Optional[UUID]: Citrine Platform unique identifier"""
    name = properties.String("data.name")
    description = properties.Optional(properties.String(), "data.description")

    locked_by = properties.Optional(
        properties.UUID, "metadata.locked.user", serializable=False
    )
    """:Optional[UUID]: id of the user whose action cause the design space to
    be locked, if it is locked"""
    lock_time = properties.Optional(
        properties.Datetime, "metadata.locked.time", serializable=False
    )
    """:Optional[datetime]: date and time at which the resource was locked,
    if it is locked"""

    @staticmethod
    def wrap_instance(subspace_data: dict) -> dict:
        """Insert a serialized embedded design space into an entity envelope.

        This facilitates deserialization.
        """
        return {
            "data": {
                "name": subspace_data.get("name", ""),
                "description": subspace_data.get("description", ""),
                "instance": subspace_data,
            }
        }

    _response_key = None
    _project_id: Optional[UUID] = None
    _session: Optional[Session] = None
    _in_progress_statuses = ["VALIDATING", "CREATED"]
    _succeeded_statuses = ["READY"]
    _failed_statuses = ["INVALID", "ERROR"]

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        from .data_source_design_space import DataSourceDesignSpace
        from .enumerated_design_space import EnumeratedDesignSpace
        from .formulation_design_space import FormulationDesignSpace
        from .product_design_space import ProductDesignSpace
        from .hierarchical_design_space import HierarchicalDesignSpace

        return {
            "Univariate": ProductDesignSpace,
            "ProductDesignSpace": ProductDesignSpace,
            "EnumeratedDesignSpace": EnumeratedDesignSpace,
            "FormulationDesignSpace": FormulationDesignSpace,
            "DataSourceDesignSpace": DataSourceDesignSpace,
            "HierarchicalDesignSpace": HierarchicalDesignSpace,
        }[data["data"]["instance"]["type"]]

    @property
    def is_locked(self) -> bool:
        """If is_locked is true, edits to the design space will be rejected."""
        return self.locked_by is not None

    @property
    def sample_design_space_executions(self):
        """Start a Sample Design Space Execution using the current Design Space."""
        return SampleDesignSpaceExecutionCollection(
            project_id=self._project_id, design_space_id=self.uid, session=self._session
        )
