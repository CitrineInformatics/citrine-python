"""Tools for working with Descriptors."""
from abc import abstractmethod
from typing import Type, List, Mapping, Optional, Union
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine.informatics.descriptors import Descriptor, FormulationDescriptor
from citrine.resources.file_link import FileLink

__all__ = ['DataSource',
           'CSVDataSource',
           'GemTableDataSource',
           'ExperimentDataSourceRef']


class DataSource(PolymorphicSerializable['DataSource']):
    """A source of data for the AI engine.

    Data source provides a polymorphic interface for specifying different kinds of data as the
    training data for predictors and the input data for some design spaces.

    """

    @abstractmethod
    def _attrs(self) -> List[str]:
        pass  # pragma: no cover

    def __eq__(self, other):
        try:
            return all([
                self.__getattribute__(key) == other.__getattribute__(key) for key in self._attrs()
            ])
        except AttributeError:
            return False

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        if "type" not in data:
            raise ValueError("Can only get types from dicts with a 'type' key")
        types: List[Type[Serializable]] = [
            CSVDataSource, GemTableDataSource, ExperimentDataSourceRef
        ]
        res = next((x for x in types if x.typ == data["type"]), None)
        if res is None:
            raise ValueError("Unrecognized type: {}".format(data["type"]))
        return res


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

    def _attrs(self) -> List[str]:
        return ["file_link", "column_definitions", "identifiers", "typ"]

    def __init__(self,
                 *,
                 file_link: FileLink,
                 column_definitions: Mapping[str, Descriptor],
                 identifiers: Optional[List[str]] = None):
        self.file_link = file_link
        self.column_definitions = column_definitions
        self.identifiers = identifiers


class GemTableDataSource(Serializable['GemTableDataSource'], DataSource):
    """A data source based on a GEM Table hosted on the data platform.

    Parameters
    ----------
    table_id: UUID
        Unique identifier for the GEM Table
    table_version: Union[str,int]
        Version number for the GEM Table. The first GEM table built from a configuration
        has version = 1. Strings are cast to ints.
    formulation_descriptor: Optional[FormulationDescriptor]
        Optional descriptor used to store formulations emitted by the data source.
        If the data source emits a formulation but this argument is not provided, then a
        default formulation descriptor will be generated. The formulations descriptor, and
        other descriptors, can be retrieved using
        :func:`~citrine.resources.descriptors.DescriptorMethods.descriptors_from_data_source`.

    """

    typ = properties.String('type', default='hosted_table_data_source', deserializable=False)
    table_id = properties.UUID("table_id")
    table_version = properties.Integer("table_version")
    formulation_descriptor = properties.Optional(
        properties.Object(FormulationDescriptor),
        "formulation_descriptor"
    )

    def _attrs(self) -> List[str]:
        return ["table_id", "table_version", "typ"]

    def __init__(self,
                 *,
                 table_id: UUID,
                 table_version: Union[int, str],
                 formulation_descriptor: Optional[FormulationDescriptor] = None):
        self.table_id: UUID = table_id
        self.table_version: Union[int, str] = table_version
        self.formulation_descriptor: Optional[FormulationDescriptor] = formulation_descriptor


class ExperimentDataSourceRef(Serializable['ExperimentDataSourceRef'], DataSource):
    """A reference to a data source based on an experiment result hosted on the data platform.

    Parameters
    ----------
    datasource_id: UUID
        Unique identifier for the Experiment Data Source

    """

    typ = properties.String('type', default='experiments_data_source', deserializable=False)
    datasource_id = properties.UUID("datasource_id")

    def _attrs(self) -> List[str]:
        return ["datasource_id", "typ"]

    def __init__(self, *, datasource_id: UUID):
        self.datasource_id: UUID = datasource_id
