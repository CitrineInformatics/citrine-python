"""Tools for working with Descriptors."""
from abc import abstractmethod
from typing import Type, List, Union
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.resources.gemtables import GemTable

__all__ = [
    'DataSource',
    'GemTableDataSource',
    'ExperimentDataSourceRef',
    'SnapshotDataSource',
]


class DataSource(PolymorphicSerializable['DataSource']):
    """A source of data for the AI engine.

    Data source provides a polymorphic interface for specifying different kinds of data as the
    training data for predictors and the input data for some design spaces.

    """

    def __eq__(self, other):
        if isinstance(other, Serializable):
            return self.dump() == other.dump()
        else:
            return False

    @classmethod
    def _subclass_list(self) -> list[type[Serializable]]:
        return [GemTableDataSource, ExperimentDataSourceRef, SnapshotDataSource]

    @classmethod
    def get_type(cls, data) -> type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        res = next((x for x in cls._subclass_list() if x.typ == data["type"]), None)
        if res is None:
            raise ValueError(f"Unrecognized type: {data['type']}")
        return res

    @property
    @abstractmethod
    def _data_source_type(self) -> str:
        """The data source type string, which is the leading term of the data_source_id."""

    @classmethod
    def from_data_source_id(cls, data_source_id: str) -> "DataSource":
        """Build a DataSource from a datasource_id."""
        terms = data_source_id.split("::")
        res = next((x for x in cls._subclass_list() if x._data_source_type == terms[0]), None)
        if res is None:
            raise ValueError(f"Unrecognized type: {terms[0]}")
        return res._data_source_id_builder(*terms[1:])

    @classmethod
    @abstractmethod
    def _data_source_id_builder(cls, *args) -> "DataSource":
        """Build a DataSource based on a parsed data_source_id."""

    @abstractmethod
    def to_data_source_id(self) -> str:
        """Generate the data_source_id for this DataSource."""


class GemTableDataSource(Serializable['GemTableDataSource'], DataSource):
    """A data source based on a GEM Table hosted on the data platform.

    Parameters
    ----------
    table_id: UUID
        Unique identifier for the GEM Table
    table_version: str | int
        Version number for the GEM Table. The first GEM table built from a configuration
        has version = 1. Strings are cast to ints.

    """

    typ = properties.String('type', default='hosted_table_data_source', deserializable=False)
    table_id = properties.UUID("table_id")
    table_version = properties.Integer("table_version")

    _data_source_type = "gemd"

    def __init__(self,
                 *,
                 table_id: UUID,
                 table_version: int | str):
        self.table_id: UUID = table_id
        self.table_version: int | str = table_version

    @classmethod
    def _data_source_id_builder(cls, *args) -> DataSource:
        return GemTableDataSource(table_id=UUID(args[0]), table_version=args[1])

    def to_data_source_id(self) -> str:
        """Generate the data_source_id for this DataSource."""
        return f"{self._data_source_type}::{self.table_id}::{self.table_version}"

    @classmethod
    def from_gemtable(cls, table: GemTable) -> "GemTableDataSource":
        """Generate a DataSource that corresponds to a GemTable.

        Parameters
        ----------
        table: GemTable
            The GemTable object to reference

        """
        return GemTableDataSource(table_id=table.uid, table_version=table.version)


class ExperimentDataSourceRef(Serializable['ExperimentDataSourceRef'], DataSource):
    """A reference to a data source based on an experiment result hosted on the data platform.

    Parameters
    ----------
    datasource_id: UUID
        Unique identifier for the Experiment Data Source

    """

    typ = properties.String('type', default='experiments_data_source', deserializable=False)
    datasource_id = properties.UUID("datasource_id")

    _data_source_type = "experiments"

    def __init__(self, *, datasource_id: UUID):
        self.datasource_id: UUID = datasource_id

    @classmethod
    def _data_source_id_builder(cls, *args) -> DataSource:
        return ExperimentDataSourceRef(datasource_id=UUID(args[0]))

    def to_data_source_id(self) -> str:
        """Generate the data_source_id for this DataSource."""
        return f"{self._data_source_type}::{self.datasource_id}"


class SnapshotDataSource(Serializable['SnapshotDataSource'], DataSource):
    """A reference to a data source based on a Snapshot on the data platform.

    Parameters
    ----------
    snapshot_id: UUID
        Unique identifier for the Snapshot Data Source

    """

    typ = properties.String('type', default='snapshot_data_source', deserializable=False)
    snapshot_id = properties.UUID("snapshot_id")

    _data_source_type = "snapshot"

    def __init__(self, *, snapshot_id: UUID):
        self.snapshot_id = snapshot_id

    @classmethod
    def _data_source_id_builder(cls, *args) -> DataSource:
        return SnapshotDataSource(snapshot_id=UUID(args[0]))

    def to_data_source_id(self) -> str:
        """Generate the data_source_id for this DataSource."""
        return f"{self._data_source_type}::{self.snapshot_id}"
