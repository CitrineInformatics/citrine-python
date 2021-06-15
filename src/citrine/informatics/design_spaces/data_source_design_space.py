from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine.informatics.data_sources import DataSource
from citrine.informatics.design_spaces.design_space import DesignSpace
from citrine._rest.ai_resource_metadata import AIResourceMetadata

__all__ = ['DataSourceDesignSpace']


class DataSourceDesignSpace(Resource['DataSourceDesignSpace'], DesignSpace, AIResourceMetadata):
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

    _resource_type = ResourceTypeEnum.MODULE

    data_source = properties.Object(DataSource, 'config.data_source')

    typ = properties.String('config.type', default='DataSourceDesignSpace', deserializable=False)
    module_type = properties.String('module_type', default='DESIGN_SPACE', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 data_source: DataSource):
        self.name: str = name
        self.description: str = description
        self.data_source: DataSource = data_source

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<DataSourceDesignSpace {!r}>'.format(self.name)
