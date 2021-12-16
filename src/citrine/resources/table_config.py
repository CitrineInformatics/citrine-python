from copy import copy
from typing import List, Union, Optional, Tuple
from uuid import UUID

from deprecation import deprecated
from gemd.entity.object import MaterialRun

from gemd.entity.link_by_uid import LinkByUID
from gemd.enumeration.base_enumeration import BaseEnumeration

from citrine._rest.collection import Collection
from citrine._rest.resource import Resource, ResourceTypeEnum
from citrine._serialization import properties
from citrine._session import Session
from citrine._utils.functions import migrate_deprecated_argument, format_escaped_url
from citrine.resources.data_concepts import CITRINE_SCOPE, _make_link_by_uid
from citrine.resources.process_template import ProcessTemplate
from citrine.gemtables.columns import Column, MeanColumn, IdentityColumn, OriginalUnitsColumn, \
    ConcatColumn
from citrine.gemtables.rows import Row
from citrine.gemtables.variables import Variable, IngredientIdentifierByProcessTemplateAndName, \
    IngredientQuantityByProcessAndName, IngredientQuantityDimension, \
    IngredientIdentifierInOutput, IngredientQuantityInOutput, \
    IngredientLabelsSetByProcessAndName, IngredientLabelsSetInOutput


class TableBuildAlgorithm(BaseEnumeration):
    """[ALPHA] The algorithm to use in automatically building a Table Configuration.

    * SINGLE_ROW corresponds one row per material history
    * FORMULATIONS corresponds to one row per ingredient, intermediate, or terminal
      material, splitting the graph at branches.
    """

    SINGLE_ROW = "single_row"
    FORMULATIONS = "formulations"


class TableConfig(Resource["TableConfig"]):
    """
    [ALPHA] The Table Configuration used to build GEM Tables.

    Parameters
    ----------
    name: str
        Name of the Table Configuration
    description: str
        Description of the Table Configuration
    datasets: list[UUID]
        Datasets that are in scope for the table, as a list of dataset uuids
    variables: list[Variable]
        Variable definitions, which define data from the material histories to use in the columns
    rows: list[Row]
        List of row definitions that define the rows of the table
    columns: list[Column]
        Column definitions, which describe how the variables are shaped into the table

    """

    # FIXME (DML): rename this (this is dependent on the server side)
    _response_key = "ara_definition"
    _resource_type = ResourceTypeEnum.TABLE_DEFINITION

    @staticmethod
    def _get_dups(lst: List) -> List:
        # Hmmn, this looks like a potentially costly operation?!
        return [x for x in lst if lst.count(x) > 1]

    config_uid = properties.Optional(properties.UUID(), 'definition_id')
    """:Optional[UUID]: Unique ID of the table config, independent of its version."""
    version_number = properties.Optional(properties.Integer, 'version_number')
    """:Optional[int]: The version of the table config, starting from 1.
    It increases every time the table config is updated."""
    version_uid = properties.Optional(properties.UUID(), 'id')
    """:Optional[UUID]: Unique ID that specifies one version of one table config."""

    name = properties.String("name")
    description = properties.String("description")
    datasets = properties.List(properties.UUID, "datasets")
    variables = properties.List(properties.Object(Variable), "variables")
    rows = properties.List(properties.Object(Row), "rows")
    columns = properties.List(properties.Object(Column), "columns")

    def __init__(self, name: str, *, description: str, datasets: List[UUID],
                 variables: List[Variable], rows: List[Row], columns: List[Column]):
        self.name = name
        self.description = description
        self.datasets = datasets
        self.rows = rows
        self.variables = variables
        self.columns = columns

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

    @property
    def uid(self) -> UUID:
        """Unique ID of the table config, independent of its version."""
        return self.config_uid

    @uid.setter
    def uid(self, new_uid: Union[str, UUID]) -> None:
        """Set the unique ID of the table config, independent of its version."""
        self.config_uid = new_uid

    def add_columns(self, *,
                    variable: Variable,
                    columns: List[Column],
                    name: Optional[str] = None,
                    description: Optional[str] = None
                    ) -> 'TableConfig':
        """[ALPHA] Add a variable and one or more columns to this TableConfig (out-of-place).

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

        new_config = TableConfig(
            name=name or self.name,
            description=description or self.description,
            datasets=copy(self.datasets),
            rows=copy(self.rows),
            variables=copy(self.variables) + [variable],
            columns=copy(self.columns) + columns
        )
        new_config.version_number = copy(self.version_number)
        new_config.config_uid = copy(self.config_uid)
        new_config.version_uid = copy(self.version_uid)
        return new_config

    def add_all_ingredients(self, *,
                            process_template: Union[LinkByUID, ProcessTemplate, str, UUID],
                            project,
                            quantity_dimension: IngredientQuantityDimension,
                            scope: str = CITRINE_SCOPE,
                            unit: Optional[str] = None
                            ):
        """[ALPHA] Add variables and columns for all of the possible ingredients in a process.

        For each allowed ingredient name in the process template there is a column for the id of
        the ingredient, id for ingredient labels, and a column for the quantity of the ingredient.
        If the quantities are given in absolute amounts then there is also a column for units.

        Parameters
        ------------
        process_template: Union[LinkByUID, ProcessTemplate, str, UUID]
            representation of a registered process template
        project: Project
            a project that has access to the process template
        quantity_dimension: IngredientQuantityDimension
            the dimension in which to report ingredient quantities
        scope: Optional[str]
            the scope for which to get ingredient ids (default is Citrine scope, 'id')
        unit: Optional[str]
            the units for the quantity, if selecting Absolute Quantity

        """
        dimension_display = {
            IngredientQuantityDimension.ABSOLUTE: "absolute quantity",
            IngredientQuantityDimension.MASS: "mass fraction",
            IngredientQuantityDimension.VOLUME: "volume fraction",
            IngredientQuantityDimension.NUMBER: "number fraction"
        }
        link = _make_link_by_uid(process_template)
        process: ProcessTemplate = project.process_templates.get(uid=link)
        if not process.allowed_names:
            raise RuntimeError(
                "Cannot add ingredients for process template \'{}\' because it has no defined "
                "ingredients (allowed_names is not defined).".format(process.name))

        new_variables = []
        new_columns = []
        for name in process.allowed_names:
            identifier_variable = IngredientIdentifierByProcessTemplateAndName(
                name='_'.join([process.name, name, str(hash(link.id + name + scope))]),
                headers=[process.name, name, scope],
                process_template=link,
                ingredient_name=name,
                scope=scope
            )
            quantity_variable = IngredientQuantityByProcessAndName(
                name='_'.join([process.name, name, str(hash(
                    link.id + name + dimension_display[quantity_dimension]))]),
                headers=[process.name, name, dimension_display[quantity_dimension]],
                process_template=link,
                ingredient_name=name,
                quantity_dimension=quantity_dimension,
                unit=unit
            )
            label_variable = IngredientLabelsSetByProcessAndName(
                name='_'.join([process.name, name, str(hash(
                    link.id + name + 'Labels'))]),
                headers=[process.name, name, 'Labels'],
                process_template=link,
                ingredient_name=name,
            )

            if identifier_variable.name not in [var.name for var in self.variables]:
                new_variables.append(identifier_variable)
                new_columns.append(IdentityColumn(data_source=identifier_variable.name))
            new_variables.append(quantity_variable)
            new_columns.append(MeanColumn(data_source=quantity_variable.name))
            if quantity_dimension == IngredientQuantityDimension.ABSOLUTE:
                new_columns.append(OriginalUnitsColumn(data_source=quantity_variable.name))
            if label_variable.name not in [var.name for var in self.variables]:
                new_variables.append(label_variable)
                new_columns.append(
                    ConcatColumn(
                        data_source=label_variable.name,
                        subcolumn=IdentityColumn(data_source=label_variable.name)
                    )
                )

        new_config = TableConfig(
            name=self.name,
            description=self.description,
            datasets=copy(self.datasets),
            rows=copy(self.rows),
            variables=copy(self.variables) + new_variables,
            columns=copy(self.columns) + new_columns
        )
        new_config.version_number = copy(self.version_number)
        new_config.config_uid = copy(self.config_uid)
        new_config.version_uid = copy(self.version_uid)
        return new_config

    def add_all_ingredients_in_output(self, *,
                                      process_templates: List[LinkByUID],
                                      project,
                                      quantity_dimension: IngredientQuantityDimension,
                                      scope: str = CITRINE_SCOPE,
                                      unit: Optional[str] = None
                                      ):
        """[ALPHA] Add variables and columns for all possible ingredients in a list of processes.

        For each allowed ingredient name in the union of all passed process templates there is a
        column for the id of the ingredient and a column for the quantity of the ingredient.
        Columns are filled with the "InOutput" method halting at any of the passed process
        templates. If the quantities are given in absolute amounts then there is also a column for
        units.

        Parameters
        ------------
        process_templates: List[LinkByUID]
            registered process templates from which to pull allowed ingredients and at which to
            halt searching
        project: Project
            a project that has access to the process template
        quantity_dimension: IngredientQuantityDimension
            the dimension in which to report ingredient quantities
        scope: Optional[str]
            the scope for which to get ingredient ids (default is Citrine scope, 'id')
        unit: Optional[str]
            the units for the quantity, if selecting Absolute Quantity

        """
        dimension_display = {
            IngredientQuantityDimension.ABSOLUTE: "absolute quantity",
            IngredientQuantityDimension.MASS: "mass fraction",
            IngredientQuantityDimension.VOLUME: "volume fraction",
            IngredientQuantityDimension.NUMBER: "number fraction"
        }
        union_allowed_names = []
        for process_template_link in process_templates:
            process: ProcessTemplate = project.process_templates.get(process_template_link)
            if not process.allowed_names:
                raise RuntimeError(
                    f"Cannot add ingredients for process template '{process.name}' "
                    "because it has no defined ingredients (allowed_names is not defined)"
                )
            else:
                union_allowed_names = list(set(union_allowed_names) | set(process.allowed_names))

        new_variables = []
        new_columns = []
        for name in union_allowed_names:
            identifier_variable = IngredientIdentifierInOutput(
                name='_'.join([name, str(hash(name + scope))]),
                headers=[name, scope],
                process_templates=process_templates,
                ingredient_name=name,
                scope=scope
            )
            quantity_variable = IngredientQuantityInOutput(
                name='_'.join([name, str(hash(name + dimension_display[quantity_dimension]))]),
                headers=[name, dimension_display[quantity_dimension]],
                process_templates=process_templates,
                ingredient_name=name,
                quantity_dimension=quantity_dimension,
                unit=unit
            )
            label_variable = IngredientLabelsSetInOutput(
                name='_'.join([name, str(hash(name + 'Labels'))]),
                headers=[name, 'Labels'],
                process_templates=process_templates,
                ingredient_name=name,
            )

            if identifier_variable.name not in [var.name for var in self.variables]:
                new_variables.append(identifier_variable)
                new_columns.append(IdentityColumn(data_source=identifier_variable.name))
            new_variables.append(quantity_variable)
            new_columns.append(MeanColumn(data_source=quantity_variable.name))
            if quantity_dimension == IngredientQuantityDimension.ABSOLUTE:
                new_columns.append(OriginalUnitsColumn(data_source=quantity_variable.name))
            if label_variable.name not in [var.name for var in self.variables]:
                new_variables.append(label_variable)
                new_columns.append(
                    ConcatColumn(
                        data_source=label_variable.name,
                        subcolumn=IdentityColumn(data_source=label_variable.name)
                    )
                )

        new_config = TableConfig(
            name=self.name,
            description=self.description,
            datasets=copy(self.datasets),
            rows=copy(self.rows),
            variables=copy(self.variables) + new_variables,
            columns=copy(self.columns) + new_columns
        )
        new_config.version_number = copy(self.version_number)
        new_config.config_uid = copy(self.config_uid)
        new_config.version_uid = copy(self.version_uid)
        return new_config


class TableConfigCollection(Collection[TableConfig]):
    """[ALPHA] Represents the collection of all Table Configs associated with a project."""

    # FIXME (DML): use newly named properties when they're available
    _path_template = 'projects/{project_id}/ara-definitions'
    _collection_key = 'definitions'
    _resource = TableConfig

    # NOTE: This isn't actually an 'individual key' - both parts (version and
    # definition) are necessary
    _individual_key = None

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def get(self, uid: Union[UUID, str], *, version: Optional[int] = None):
        """[ALPHA] Get a table config.

        If no version is specified, then the most recent version is returned.

        """
        if uid is None:
            raise ValueError("Cannot get when uid=None.  Are you using a registered resource?")
        if version is not None:
            path = self._get_path(uid) + format_escaped_url("/versions/{}", version)
            data = self.session.get_resource(path)
        else:
            path = self._get_path(uid)
            data = self.session.get_resource(path)
            version_numbers = [version_data['version_number'] for version_data in data['versions']]
            index = version_numbers.index(max(version_numbers))
            data['version'] = data['versions'][index]
        return self.build(data)

    def get_for_table(self, table: "GemTable") -> TableConfig:  # noqa: F821
        """
        Get the TableConfig used to build the given table.

        Parameters
        ----------
        table: GemTable
            Table for which to get the config.

        Returns
        -------
        TableConfig
            The table config used to produce the given table.

        """
        # the route to fetch the config is built off the display table route tree
        path = 'projects/{project_id}/display-tables/{uid}/versions/{version}/definition'.format(
            project_id=self.project_id, uid=table.uid, version=table.version)
        data = self.session.get_resource(path)
        return self.build(data)

    @deprecated(deprecated_in="0.124.0", removed_in="2.0.0",
                details="get_with_version() is deprecated in favor of get()")
    def get_with_version(self, *, table_config_uid: Union[UUID, str],
                         version_number: int) -> TableConfig:
        """[ALPHA] Get a Table Config at a specific version."""
        return self.get(uid=table_config_uid, version=version_number)  # pragma: no cover

    def build(self, data: dict) -> TableConfig:
        """[ALPHA] Build an individual Table Config from a dictionary."""
        version_data = data['version']
        table_config = TableConfig.build(version_data['ara_definition'])
        table_config.version_number = version_data['version_number']
        table_config.version_uid = version_data['id']
        table_config.config_uid = data['definition']['id']
        table_config.project_id = self.project_id
        table_config.session = self.session
        return table_config

    def default_for_material(
            self, *,
            material: Union[MaterialRun, LinkByUID, str, UUID],
            name: str,
            description: str = None,
            algorithm: Optional[TableBuildAlgorithm] = None,
            scope: str = None
    ) -> Tuple[TableConfig, List[Tuple[Variable, Column]]]:
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
        material: Union[MaterialRun, LinkByUid, str, UUID]
            The terminal material whose history is used to construct a table config.
        name: str
            The name for the table config.
        description: str, optional
            The description of the table config. Defaults to autogenerated message.
        algorithm: TableBuildAlgorithm, optional
            The algorithm to use in generating a Table Configuration from the sample material
            history.  If unspecified, uses the webservice's default.
        scope: str, optional
            [DEPRECATED] Use a LinkByUID instead.
            The scope of the material id. If a uid is provided and scope is not specified,
            then the uid is assumed to be a Citrine ID.

        Returns
        -------
        List[Tuple[Variable, Column]]
            A table config as well as addition variables/columns which would result in
            ambiguous matches if included in the config.


        """
        link = _make_link_by_uid(material, scope)
        params = {
            'id': link.id,
            'scope': link.scope,
            'name': name,
        }
        if description is not None:
            params['description'] = description
        if algorithm is not None:
            if isinstance(algorithm, TableBuildAlgorithm):
                params['algorithm'] = algorithm.value
            else:  # Not per spec, but be forgiving
                params['algorithm'] = str(algorithm)
        data = self.session.get_resource(
            format_escaped_url('projects/{}/table-configs/default', self.project_id),
            params=params,
        )
        config = TableConfig.build(data['config'])
        ambiguous = [(Variable.build(v), Column.build(c)) for v, c in data['ambiguous']]
        return config, ambiguous

    def preview(self, *,
                table_config: TableConfig,
                preview_materials: List[LinkByUID] = None,
                preview_roots: List[LinkByUID] = None
                ) -> dict:
        """[ALPHA] Preview a Table Config on an explicit set of terminal materials.

        Parameters
        ----------
        table_config: TableConfig
            Table Config to preview
        preview_materials: List[LinkByUID]
            List of links to the material runs to use as terminal materials in the preview
        preview_roots: List[LinkByUID]
            [DEPRECATED] Use preview_materials instead

        """
        preview_materials = migrate_deprecated_argument(preview_materials, "preview_materials",
                                                        preview_roots, "preview_roots")
        path = self._get_path() + "/preview"
        body = {
            "definition": table_config.dump(),
            "rows": [x.as_dict() for x in preview_materials]
        }
        return self.session.post_resource(path, body)

    def register(self, table_config: TableConfig) -> TableConfig:
        """[ALPHA] Register a Table Config.

        If the provided TableConfig does not have a definition_uid, create a new element of the
        TableConfigCollection by registering the provided TableConfig. If the provided
        TableConfig does have a uid, update (replace) the TableConfig at that uid with the
        provided TableConfig.

        :param table_config: The TableConfig to register

        :return: The registered TableConfig with updated metadata

        TODO: Consider validating that a resource exists at the given uid before updating.
            The code to do so is not yet implemented on the backend
        """
        # TODO: This is dumping our TableConfig (which encapsulates both
        #  the table config properties, versioned table config properties, as well as the
        #  underlying table config JSON blob) into the Table Config's JSON blob ('definition')
        #  - probably not ideal.
        body = {"definition": table_config.dump()}
        if table_config.config_uid is None:
            data = self.session.post_resource(self._get_path(), body)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)
        else:
            # Implement update as a part of register both because:
            # 1) The validation requirements are the same for updating and registering an
            #    TableConfig
            # 2) This prevents users from accidentally registering duplicate Table Configs
            data = self.session.put_resource(self._get_path(table_config.config_uid), body)
            data = data[self._individual_key] if self._individual_key else data
            return self.build(data)

    def update(self, table_config: TableConfig) -> TableConfig:
        """
        [ALPHA] Update a Table Config.

        If the provided Table Config does have a uid, update (replace) the Table Config at that
        uid with the provided TableConfig.

        Raise a ValueError if the provided Table Config does not have a config_uid.

        :param table_config: The Table Config to updated
        :return: The updated Table Config with updated metadata
        """
        if table_config.config_uid is None:
            raise ValueError("Cannot update Table Config without a config_uid."
                             " Please either use register() to initially register this"
                             " Table Config or retrieve the registered details before calling"
                             " update()")
        return self.register(table_config)

    def delete(self, uid: Union[UUID, str]):
        """Table configs cannot be deleted at this time."""
        raise NotImplementedError("Table configs cannot be deleted at this time.")
