from typing import List, Union, Optional
from uuid import UUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.ara.columns import Column
from citrine.ara.rows import Row
from citrine.ara.variables import Variable


class AraDefinition(Resource["AraDefinition"]):
    """
    The definition of an Ara Table.

    Parameters
    ----------
    name: str
        Name of the table being defined
    description: str
        Description of the table being defined
    datasets: list[UUID]
        Datasets that are in scope for the table, as a list of dataset uuids
    variables: list[Variable]
        Variable definitions, which define data from the material histories to use in the columns
    rows: list[Row]
        List of row definitions that define the rows of the table
    columns: list[Column]
        Column definitions, which describe how the variables are shaped into the table

    """

    _response_key = "ara_definition"

    @staticmethod
    def _get_dups(lst: List) -> List:
        return [x for x in lst if lst.count(x) > 1]

    uid = properties.Optional(properties.UUID(), 'id')
    version = properties.Optional(properties.Integer, 'version')
    name = properties.String("name")
    description = properties.String("description")
    datasets = properties.List(properties.UUID, "datasets")
    variables = properties.List(properties.Object(Variable), "variables")
    rows = properties.List(properties.Object(Row), "rows")
    columns = properties.List(properties.Object(Column), "columns")

    def __init__(self, *, name: str, description: str, datasets: List[UUID],
                 variables: List[Variable], rows: List[Row], columns: List[Column],
                 uid: Optional[UUID] = None, version: Optional[int] = None):
        self.name = name
        self.description = description
        self.datasets = datasets
        self.rows = rows
        self.variables = variables
        self.columns = columns
        self.uid = uid
        self.version = version

        # Note that these validations only apply at construction time. The current intended usage
        # is for this object to be created holistically; if changed, then these will need
        # to move into setters.
        names = [x.name for x in variables]
        dup_names = self._get_dups(names)
        if len(dup_names) > 0:
            raise ValueError("Multiple variables defined these names,"
                             " which much be unique: {}".format(dup_names))
        headers = [x.headers for x in variables]
        dup_headers = self._get_dups(headers)
        if len(dup_headers) > 0:
            raise ValueError("Multiple variables defined these output_names,"
                             " which much be unique: {}".format(dup_headers))

        missing_variables = [x.data_source for x in columns if x.data_source not in names]
        if len(missing_variables) > 0:
            raise ValueError("The data_source of the columns must match one of the variable names,"
                             " but {} were missing".format(missing_variables))


class AraDefinitionCollection(Collection[AraDefinition]):
    """Represents the collection of all Ara Definitions associated with a project."""

    _path_template = 'projects/{project_id}/ara_definitions'

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def get(self, uid: Union[UUID, str], version: int) -> AraDefinition:
        """Get an Ara Definition."""
        path = self._get_path(uid) + "/versions/{}".format(version)
        data = self.session.get_resource(path)
        return self.build(data)

    def build(self, data: dict) -> AraDefinition:
        """Build an individual Ara Definition from a dictionary."""
        defn = AraDefinition.build(data)
        defn.project_id = self.project_id
        defn.session = self.session
        return defn
