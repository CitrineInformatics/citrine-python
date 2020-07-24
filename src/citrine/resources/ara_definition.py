from copy import copy
from logging import getLogger
from typing import List, Union, Optional, Tuple
from uuid import UUID

from deprecation import deprecated
from gemd.entity.object import MaterialRun

from citrine.resources.ara_job import JobSubmissionResponse, JobStatusResponse
from gemd.entity.link_by_uid import LinkByUID

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource
from citrine._serialization import properties
from citrine._session import Session
from citrine.resources.process_template import ProcessTemplate  # noqa: F401
from citrine.ara.columns import Column, MeanColumn, IdentityColumn, OriginalUnitsColumn
from citrine.ara.rows import Row
from citrine.ara.variables import Variable, IngredientIdentifierByProcessTemplateAndName, \
    IngredientQuantityByProcessAndName, IngredientQuantityDimension

logger = getLogger(__name__)


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
        # Hmmn, this looks like a potentially costly operation?!
        return [x for x in lst if lst.count(x) > 1]

    definition_uid = properties.Optional(properties.UUID(), 'definition_id')
    version_uid = properties.Optional(properties.UUID(), 'id')
    version_number = properties.Optional(properties.Integer, 'version_number')
    name = properties.String("name")
    description = properties.String("description")
    datasets = properties.List(properties.UUID, "datasets")
    variables = properties.List(properties.Object(Variable), "variables")
    rows = properties.List(properties.Object(Row), "rows")
    columns = properties.List(properties.Object(Column), "columns")

    def __init__(self, *, name: str, description: str, datasets: List[UUID],
                 variables: List[Variable], rows: List[Row], columns: List[Column],
                 version_uid: Optional[UUID] = None, version_number: Optional[int] = None,
                 definition_uid: Optional[UUID] = None):
        self.name = name
        self.description = description
        self.datasets = datasets
        self.rows = rows
        self.variables = variables
        self.columns = columns
        self.version_uid = version_uid
        self.version_number = version_number
        self.definition_uid = definition_uid

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

    def add_all_ingredients(self, *,
                            process_template: LinkByUID,
                            project,
                            quantity_dimension: IngredientQuantityDimension,
                            scope: str = 'id'
                            ):
        """[ALPHA] Add variables and columns for all of the possible ingredients in a process.

        For each allowed ingredient name in the process template there is a column for the if of
        the ingredient and a column for the quantity of the ingredient. If the quantities are
        given in absolute amounts then there is also a column for units.

        Parameters
        ------------
        process_template: LinkByUID
            scope and id of a registered process template
        project: Project
            a project that has access to the process template
        quantity_dimension: IngredientQuantityDimension
            the dimension in which to report ingredient quantities
        scope: Optional[str]
            the scope for which to get ingredient ids (default is Citrine scope, 'id')

        """
        dimension_display = {
            IngredientQuantityDimension.ABSOLUTE: "absolute quantity",
            IngredientQuantityDimension.MASS: "mass fraction",
            IngredientQuantityDimension.VOLUME: "volume fraction",
            IngredientQuantityDimension.NUMBER: "number fraction"
        }
        process: ProcessTemplate = project.process_templates.get(
            uid=process_template.id, scope=process_template.scope)
        if not process.allowed_names:
            raise RuntimeError(
                "Cannot add ingredients for process template \'{}\' because it has no defined "
                "ingredients (allowed_names is not defined).".format(process.name))

        new_variables = []
        new_columns = []
        for name in process.allowed_names:
            identifier_variable = IngredientIdentifierByProcessTemplateAndName(
                name='_'.join([process.name, name, str(hash(process_template.id + name + scope))]),
                headers=[process.name, name, scope],
                process_template=process_template,
                ingredient_name=name,
                scope=scope
            )
            quantity_variable = IngredientQuantityByProcessAndName(
                name='_'.join([process.name, name, str(hash(
                    process_template.id + name + dimension_display[quantity_dimension]))]),
                headers=[process.name, name, dimension_display[quantity_dimension]],
                process_template=process_template,
                ingredient_name=name,
                quantity_dimension=quantity_dimension
            )

            if identifier_variable.name not in [var.name for var in self.variables]:
                new_variables.append(identifier_variable)
                new_columns.append(IdentityColumn(data_source=identifier_variable.name))
            new_variables.append(quantity_variable)
            new_columns.append(MeanColumn(data_source=quantity_variable.name))
            if quantity_dimension == IngredientQuantityDimension.ABSOLUTE:
                new_columns.append(OriginalUnitsColumn(data_source=quantity_variable.name))

        return AraDefinition(
            name=self.name,
            description=self.description,
            datasets=copy(self.datasets),
            rows=copy(self.rows),
            variables=copy(self.variables) + new_variables,
            columns=copy(self.columns) + new_columns
        )


class AraDefinitionCollection(Collection[AraDefinition]):
    """[ALPHA] Represents the collection of all Ara Definitions associated with a project."""

    _path_template = 'projects/{project_id}/ara-definitions'
    _collection_key = 'definitions'
    _resource = AraDefinition

    # NOTE: This isn't actually an 'individual key' - both parts (version and
    # definition) are necessary
    _individual_key = None

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def get_with_version(self, definition_uid: Union[UUID, str],
                         version_number: int) -> AraDefinition:
        """[ALPHA] Get an Ara Definition at a specific version."""
        path = self._get_path(definition_uid) + "/versions/{}".format(version_number)
        data = self.session.get_resource(path)
        data = data[self._individual_key] if self._individual_key else data
        return self.build(data)

    def build(self, data: dict) -> AraDefinition:
        """[ALPHA] Build an individual Ara Definition from a dictionary."""
        version_data = data['version']
        defn = AraDefinition.build(version_data['ara_definition'])
        defn.version_number = version_data['version_number']
        defn.version_uid = version_data['id']
        defn.definition_uid = data['definition']['id']
        defn.project_id = self.project_id
        defn.session = self.session
        return defn

    def default_for_material(
            self, *, material: Union[MaterialRun, str, UUID],
            name: str, description: str = None, scope: str = None
    ) -> Tuple[AraDefinition, List[Tuple[Variable, Column]]]:
        """
        [ALPHA] Build best-guess default table config for provided terminal material's history.

        Currently generates variables for each templated attribute in the material history in
        either AttributeByTemplate, or if possible AttributeByTemplateAndObjectTemplate.
        Attributes on object templates used in the history are included regardless of their
        presence on data objects in the history. Additionally, each quantity dimension specified on
        ingredients in the material history will be captured in IngredientQuantityByProcessAndName.

        If a generated variable would match ambiguously on the given material history, it is
        excluded from the generated config and included in the second part of the returned tuple.

        Parameters
        ----------
        material: Union[MaterialRun, str, UUID]
            The terminal material whose history is used to construct a table config.
        name: str
            The name for the table config.
        description: str, optional
            The description of the table config. Defaults to autogenerated message.
        scope: str, optional
            The scope of the material id. Need not be specified if the material is an actual
            persisted instance of material run, or if it is a Citrine ID.

        Returns A table config as well as addition variables/columns which would result in
            ambiguous matches if included in the config.
        -------

        """
        if isinstance(material, MaterialRun):
            if scope is not None:
                logger.warning(
                    'Ignoring scope {} since material run object was specified.'.format(scope))
            uid_tup = next(iter(material.uids.items()), None)
            if uid_tup is None:
                raise ValueError('Material must have a uid to build default table config.')
            scope, uid = uid_tup
        elif isinstance(material, (str, UUID)):
            uid = str(material)
            scope = scope or 'id'
        else:
            raise TypeError(  # pragma: no cover
                'material must be one of MaterialRun, str, or UUID but was {}'
                .format(type(material)))
        params = {
            'id': uid,
            'scope': scope,
            'name': name,
        }
        if description is not None:
            params['description'] = description
        data = self.session.get_resource(
            'projects/{}/table-configs/default'.format(self.project_id),
            params=params,
        )
        config = AraDefinition.build(data['config'])
        ambiguous = [(Variable.build(v), Column.build(c)) for v, c in data['ambiguous']]
        return config, ambiguous

    @deprecated(details='Please use TableCollection.build_from config or '
                        'TableCollection.initiate_build')
    def build_ara_table(self, ara_def: AraDefinition) -> JobSubmissionResponse:
        """[ALPHA] submit an ara table construction job.

        This method makes a call out to the job framework to start a new job to build
        the respective table for a given AraDefinition.

        Parameters
        ----------
        ara_def: AraDefinition
            the ara definition describing the new table

        """
        from citrine.resources.table import TableCollection
        table_collection = TableCollection(self.project_id, self.session)
        return table_collection.initiate_build(ara_def, None)

    @deprecated(details='Table build job status does not have a stable format. Please use '
                        'TableCollection.build_from_config or TableCollection.get_by_build_job')
    def get_job_status(self, job_id: str):
        """[ALPHA] get status of a running job.

        This method grabs a JobStatusResponse object for the given job_id.

        Parameters
        ----------
        job_id: str
            The job we retrieve the status for

        """
        url_suffix: str = "/execution/job-status?job_id={job_id}"
        path: str = 'projects/{project_id}'.format(
            project_id=self.project_id
        ) + url_suffix.format(job_id=job_id)
        response: dict = self.session.get_resource(path=path)
        return JobStatusResponse.build(response)

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

    def register(self, defn: AraDefinition) -> AraDefinition:
        """[ALPHA] Register an Ara Definition.

        If the provided AraDefinition does not have a definition_uid, create a new element of the
        AraDefinitionCollection by registering the provided AraDefinition. If the provided
        AraDefinition does have a uid, update (replace) the AraDefinition at that uid with the
        provided AraDefinition.

        :param defn: The AraDefinition to register

        :return: The registered AraDefinition with updated metadata

        TODO: Consider validating that a resource exists at the given uid before updating.
            The code to do so is not yet implemented on the backend
        """
        # TODO: This is dumping our AraDefinition (which encapsulates both
        #  the definition properties, versioned properties, as well as the
        #  definition JSON) into the Ara Definition JSON blob ('definition')
        #  - probably not ideal.
        body = {"definition": defn.dump()}
        if defn.definition_uid is None:
            data = self.session.post_resource(self._get_path(), body)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)
        else:
            # Implement update as a part of register both because:
            # 1) The validation requirements are the same for updating and registering an
            #    AraDefinition
            # 2) This prevents users from accidentally registering duplicate AraDefinitions
            data = self.session.put_resource(self._get_path(defn.definition_uid), body)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)

    def update(self, defn: AraDefinition) -> AraDefinition:
        """
        [ALPHA] Update an AraDefinition.

        If the provided AraDefinition does have a uid, update (replace) the AraDefinition at that
        uid with the provided AraDefinition.

        Raise a ValueError if the provided AraDefinition does not have a definition_uid.

        :param defn: The AraDefinition to updated
        :return: The updated AraDefinition with updated metadata
        """
        if defn.definition_uid is None:
            raise ValueError("Cannot update Ara Definition without a definition_uid."
                             " Please either use register() to initially register this"
                             " Ara Definition or retrieve the registered details before calling"
                             " update()")
        return self.register(defn)
