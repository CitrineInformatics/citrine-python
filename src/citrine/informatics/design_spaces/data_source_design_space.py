from citrine._rest.engine_resource import EngineResource
from citrine._serialization import properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces.design_space import DesignSpace

__all__ = ['DataSourceDesignSpace']


class DataSourceDesignSpace(EngineResource['DataSourceDesignSpace'], DesignSpace):
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

    data_source = properties.Object(DataSource, 'data.instance.data_source')

    typ = properties.String('data.instance.type', default='DataSourceDesignSpace',
                            deserializable=False)

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
