from copy import copy
from typing import List, Union, Optional
from uuid import UUID

from taurus.entity.link_by_uid import LinkByUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.ara.columns import Column
from citrine.ara.rows import Row
from citrine.ara.variables import Variable


class AraDefinition(Resource["AraDefinition"]):
    """
    [ALPHA] The definition of an Ara Table.

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
            raise ValueError("Multiple variables defined these headers,"
                             " which much be unique: {}".format(dup_headers))

        missing_variables = [x.data_source for x in columns if x.data_source not in names]
        if len(missing_variables) > 0:
            raise ValueError("The data_source of the columns must match one of the variable names,"
                             " but {} were missing".format(missing_variables))

    def add_columns(self, *,
                    variable: Variable,
                    columns: List[Column],
                    name: Optional[str] = None,
                    description: Optional[str] = None
                    ) -> 'AraDefinition':
        """[ALPHA] Add a variable and one or more columns to this AraDefinition (out-of-place).

        This method checks that the variable name is not already in use and that the columns
        only reference that variable.  It is *not* able to check if the columns and the variable
        are compatible (yet, at least).

        Parameters
        ----------
        variable: Variable
            Variable to add and use in the added columns
        columns: list[Column]
            Columns to add, which must only reference the added variable
        name: Optional[str]
            Optional renaming of the table
        description: Optional[str]
            Optional re-description of the table

        """
        if variable.name in [x.name for x in self.variables]:
            raise ValueError("The variable name {} is already used".format(variable.name))

        mismatched_data_source = [x for x in columns if x.data_source != variable.name]
        if len(mismatched_data_source):
            raise ValueError("Column.data_source must be {} but found {}"
                             .format(variable.name, mismatched_data_source))

        return AraDefinition(
            name=name or self.name,
            description=description or self.description,
            datasets=copy(self.datasets),
            rows=copy(self.rows),
            variables=copy(self.variables) + [variable],
            columns=copy(self.columns) + columns
        )


class AraDefinitionCollection(Collection[AraDefinition]):
    """[ALPHA] Represents the collection of all Ara Definitions associated with a project."""

    _path_template = 'projects/{project_id}/ara-definitions'

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

    def preview(self, defn: AraDefinition, preview_roots: List[LinkByUID]) -> dict:
        """[ALPHA] Preview an AraDefinition on an explicit set of roots.

         Parameters
        ----------
        defn: AraDefinition
            Definition to preview
        preview_roots: list[LinkByUID]
            List of links to the material history roots to use in the preview

        """
        path = self._get_path() + "/preview"
        body = {
            "definition": defn.dump(),
            "rows": [x.as_dict() for x in preview_roots]
        }
        return self.session.post_resource(path, body)
