"""Tools for working with Descriptors."""
from abc import abstractmethod
from typing import Type, List, Mapping, Optional, Union
from uuid import UUID
from warnings import warn

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.descriptors import Descriptor
from citrine.resources.file_link import FileLink
from citrine.resources.gemtables import GemTable

__all__ = [
    'DataSource',
    'CSVDataSource',
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
    def _subclass_list(self) -> List[Type[Serializable]]:
        return [CSVDataSource, GemTableDataSource, ExperimentDataSourceRef, SnapshotDataSource]

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
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


class CSVDataSource(Serializable['CSVDataSource'], DataSource):
    """A data source based on a CSV file stored on the data platform.

    Parameters
    ----------
    file_link: FileLink
        link to the CSV file to read the data from
    column_definitions: Mapping[str, Descriptor]
        Map the column headers to the descriptors that will be used to interpret the cell contents
    identifiers: Optional[List[str]]
        List of one or more column headers whose values uniquely identify a row. These may overlap
        with ``column_definitions`` if a column should be used as data and as an identifier,
        but this is not necessary. Identifiers must be unique within a dataset. No two rows can
        contain the same value.

    """

    typ = properties.String('type', default='csv_data_source', deserializable=False)
    file_link = properties.Object(FileLink, "file_link")
    column_definitions = properties.Mapping(
        properties.String, properties.Object(Descriptor), "column_definitions")
    identifiers = properties.Optional(properties.List(properties.String), "identifiers")

    _data_source_type = "csv"

    def __init__(self,
                 *,
                 file_link: FileLink,
                 column_definitions: Mapping[str, Descriptor],
                 identifiers: Optional[List[str]] = None):
        self.file_link = file_link
        self.column_definitions = column_definitions
        self.identifiers = identifiers

    @classmethod
    def _data_source_id_builder(cls, *args) -> DataSource:
        # TODO Figure out how to populate the column definitions
        warn("A CSVDataSource was derived from a data_source_id "
             "but is missing its column_definitions and identities",
             UserWarning)
        return CSVDataSource(
            file_link=FileLink(url=args[0], filename=args[1]),
            column_definitions={}
        )

    def to_data_source_id(self) -> str:
        """Generate the data_source_id for this DataSource."""
        return f"{self._data_source_type}::{self.file_link.url}::{self.file_link.filename}"


class GemTableDataSource(Serializable['GemTableDataSource'], DataSource):
    """A data source based on a GEM Table hosted on the data platform.

    Parameters
    ----------
    table_id: UUID
        Unique identifier for the GEM Table
    table_version: Union[str,int]
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
                 table_version: Union[int, str]):
        self.table_id: UUID = table_id
        self.table_version: Union[int, str] = table_version

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
