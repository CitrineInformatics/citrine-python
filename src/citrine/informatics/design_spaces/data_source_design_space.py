from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces.subspace import DesignSubspace

__all__ = ['DataSourceDesignSpace']


class DataSourceDesignSpace(Resource['DataSourceDesignSpace'], DesignSubspace):
    """An enumeration of candidates stored in a data source.

    Parameters
    ----------
    name:str
        the name of the design space
    description:str
        the description of the design space
    data_source: DataSource
        the source of data for this design space

    """

    data_source = properties.Object(DataSource, 'data_source')

    typ = properties.String('type', default='DataSourceDesignSpace', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 data_source: DataSource):
        self.name: str = name
        self.description: str = description
        self.data_source: DataSource = data_source

    def __str__(self):
        return '<DataSourceDesignSpace {!r}>'.format(self.name)
