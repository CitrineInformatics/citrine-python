.. data_extraction:

[ALPHA] Data Extraction
=======================

GEM Tables are a component of the Citrine Platform data service that extracts data from GEMD's complex and expressive graphical representations into a tabular structure (like a CSV file) that is easier to consume in analytical contexts.
A GEM Table is defined on a set of material histories, and the rows in the resulting GEM Table are in 1-to-1 correspondence with those material histories.
Columns correspond to data about the material histories, such as the temperature measured in a kiln used at a specific manufacturing step.

Defining row and columns
------------------------

A RowDefinition object describes a mapping from a list of datasets to rows of a table by selecting a set of Material Histories.
Each Material History corresponds to exactly one row, though the Material Histories may overlap such that the same objects contribute data to multiple rows.
For example, the material histories of distinct Material Runs will map to exactly two rows even if their histories are identical up to differing Process Runs of their final baking step.
The only way to define rows right now is through :class:`~citrine.gemtables.rows.MaterialRunByTemplate`, which produces one row per Material Run associated with any of a list of material templates.

.. code-block:: python

   from citrine.gemtables.rows import MaterialRunByTemplate
   from gemd.entity.link_by_uid import LinkByUID
   row_def = MaterialRunByTemplate(
         templates=[LinkByUID(scope="templates", id="finished cookie")])

A :class:`~citrine.gemtables.variables.Variable` object specifies how to select a piece of data from each Material History.
Thus, it performs the first part of a mapping from the set of Material Histories to columns in the GEM Table.
A :class:`~citrine.gemtables.variables.Variable` is addressed locally (within a definition) by a ``name``.
A :class:`~citrine.gemtables.variables.Variable` is also labeled with ``headers``, which is a list of strings that can express a hierarchical relationship with other variables.
The headers are listed in decreasing hierarchical order: the first string indicates the broadest classification, and each subsequent string indicates a refinement of those classifications preceding it.
In the example below, a hardness measurement might also be performed on the object denoted by the ``Product`` header.
One might assign ``headers = ["Product", "Hardness"]`` to this measurement in order to relate it with the ``Density`` measurement of the same physical object.

.. code-block:: python

   from citrine.gemtables.variables import AttributeByTemplateAfterProcessTemplate
   from gemd.entity.link_by_uid import LinkByUID
   final_density = AttributeByTemplateAfterProcessTemplate(
         name = "final density",
         headers = ["Product", "Density"],
         attribute_template = LinkByUID(scope="templates", id="cookie density"),
         process_template = LinkByUID(scope="templates", id="apply glaze"))

A :class:`~citrine.gemtables.columns.Column` object describes how to transform a :class:`~citrine.gemtables.variables.Variable` into a primitive value (e.g., a real number, an integer, or a string) that can be entered into a cell in a table.
This is necessary because `GEMD Attributes`__ are more general than primitive values; they often convey uncertainty estimates, for example.

__ https://citrineinformatics.github.io/gemd-docs/specification/attributes/

.. code-block:: python

   from citrine.gemtables.columns import MeanColumn, StdDevColumn
   final_density_mean = MeanColumn(data_source="final density", target_units="g/cm^3")
   final_density_std = StdDevColumn(data_source="final density", target_units="g/cm^3")

The data_source parameter is a reference to a :class:`~citrine.gemtables.variables.Variable` for this :class:`~citrine.gemtables.columns.Column` to describe, so the value of ``data_source`` must match the ``name`` of a :class:`~citrine.gemtables.variables.Variable`.

Defining tables
---------------

The :class:`~citrine.resources.ara_definition.TableConfig` object defines how to build a GEM Table.
It specifies a list of UUIDs for datasets to query in generating the table,
a list of :class:`~citrine.gemtables.rows.Row` objects that define material histories to use as rows,
a list of :class:`~citrine.gemtables.variables.Variable` objects that specify how to extract data from those material histories,
and a list of :class:`~citrine.gemtables.columns.Column` objects to transform those variables into columns.

.. code-block:: python

   from citrine.resources.ara_definition import TableConfig
   from uuid import UUID
   table_config = TableConfig(
         name = "cookies",
         description = "Cookie densities",
         datasets = [UUID("7d040451-7cfb-45ca-9e0e-4b2b7010edd6"),
                     UUID("7cfb45ca-9e0e-4b2b-7010-edd67d040451")],
         variables = [final_density],
         rows = [row_def],
         columns = [final_density_mean, final_density_std])

Note the inclusion of two datasets above.
In general, you should have at least two datasets referenced because Objects and Templates are generally associated with different datasets.

In addition to defining variables, rows, and columns individually, there are convenience methods that simultaneously add multiple elements to an existing Table Config.
One such method is :func:`~citrine.resources.ara_definition.TableConfig.add_all_ingredients`, which creates variables and columns for every potential ingredient in a process.
The user provides a link to a process template that has a non-empty set of `allowed_names` (the allowed names of the ingredient runs and specs in the process).
This creates an id variable/column and a quantity variable/column for each allowed name.
The user specifies the dimension to report the quantity in: mass fraction, volume fraction, number fraction, or absolute quantity.
If the quantities are reported in absolute amounts then there is also a column for the units.

The code below takes the `table_config` object defined in the preceding code block and adds the ingredient amounts for a `batter mixing` process with known uid "3a308f78-e341-f39c-8076-35a2c88292ad".
Assume that the process template is accessible from a known project, `project`.

.. code-block:: python

    from citrine.gemtables.variables import IngredientQuantityDimension

    table_config = table_config.add_all_ingredients(
                                            process_template = LinkByUID('id', '3a308f78-e341-f39c-8076-35a2c88292ad'),
                                            project=project,
                                            quantity_dimension=IngredientQuantityDimension.MASS
                                            )

If the process template's allowed names includes, for example, "flour" then there will now be columns "batter mixing~flour~id" and "batter mixing~flour~mass fraction~mean."

Previewing tables
-----------------

Calling :func:`~citrine.resources.project.Project.table_configs` on a project returns an :class:`~citrine.resources.ara_definition.TableConfigCollection` object, which facilitates access to the collection of all TableConfigs visible to a Project.
Via such an object, one can preview a draft TableConfig on an explicit set of Material Histories, defined by their root materials:

For example:

.. code-block:: python

   table_configs = project.table_configs
   preview = table_configs.preview(
         table_config = table_config,
         preview_roots = [
               LinkByUID(scope="products", id="best cookie ever"),
               LinkByUID(scope="products", id="worst cookie ever")])

The preview returns a dictionary with two keys:

* The ``csv`` key will get a preview of the table in the comma-separated-values format.
* The ``warnings`` key will get a list of String-valued warnings that describe possible issues with the Table Config, e.g., that one of the columns is completely empty.

For example, if you wanted to print the warnings and then load the preview into a pandas dataframe, you could:

.. code-block:: python

   from io import StringIO
   import pandas as pd

   preview = table_configs.preview(table_config, preview_roots)
   print("\n\n".join(preview["warnings"]))
   data_frame = pd.read_csv(StringIO(preview["csv"]))

or even wrap it in a method that displays multi-row headers:

.. code-block:: python

    def resp_to_pandas(resp):
        import warnings
        from io import StringIO
        import pandas as pd
        if resp["warnings"]:
            warnings.warn("\n\n".join(resp["warnings"]))

        df = pd.read_csv(StringIO(resp["csv"]))

        headers = [x.split('~') for x in df]
        for header in headers:
            header.extend([''] * (max(len(x) for x in headers) - len(header)))

        return pd.DataFrame(df.values, columns=[x for x in np.array(headers).T])

Building and downloading tables
-------------------------------

After iteratively adjusting the TableConfig with the ``preview`` method above, the definition can be registered to save it.

.. code-block:: python

    table_config = table_configs.register(table_config)
    print("Definition registered as {}".format(table_config.definition_uid))

Registered Table Configs can be built into GEM Tables. For example:

.. code-block:: python

   table = project.tables.build_from_config(table_config)
   project.tables.read(table, "./my_table.csv")

The above will build a table, wait for the build job to complete, and save the table locally.

However, GEM Tables are sometimes large and time-consuming to build, so the build process can be performed asynchronously with the ``initiate_build`` method.
For example:

.. code-block:: python

    job = project.tables.initiate_build(table_config)

The return type of the ``initiate_build`` method is a :class:`~citrine.resources.job.JobSubmissionResponse` that contains a unique identifier for the submitted job.

The table id and version can be used to get a :class:`~citrine.resources.table.Table` resource that provides access the table.

You can also use the :class:`~citrine.resources.job.JobStatusResponse` to return the :class:`~citrine.resources.gemtables.GemTable` resource directly with the ``get_by_build_job`` method.
Just like the :class:`~citrine.resources.file_link.FileLink` resource, :class:`~citrine.resources.table.Table` does not literally contain the table but does expose a ``read`` method that will download it.

For example, once the above ``initiate_build`` method has completed:

.. code-block:: python

   # Get the table resource as an object
   table = project.tables.get_by_build_job(job)
   # Download the table
   project.tables.read(table, "./my_table.csv")

Available Row Definitions
-------------------------

Currently, GEM Tables only provide a single way to define Rows: by the :class:`~gemd.entity.template.material_template.MaterialTemplate` of the roots of the material histories that correspond to each row.

:class:`~citrine.gemtables.rows.MaterialRunByTemplate`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~citrine.gemtables.rows.MaterialRunByTemplate` class defines Rows through a list of :class:`~gemd.entity.template.material_template.MaterialTemplate`.
Every :class:`~gemd.entity.object.material_run.MaterialRun` that is assigned to any template in the list is used as the root of a  Material History to be mapped to a Row.
This is helpful when the rows correspond to classes of materials that are defined through their templates.
For example, there could be a :class:`~gemd.entity.template.material_template.MaterialTemplate` called "Cake" that is used in all
of the cakes and another called "Brownies" that is used in all of the brownies.
By including one or both of those templates, you can define a table of Cakes, Brownies, or both.

Available Variable Definitions
------------------------------

There are several ways to define variables that take their values from Attributes and identifiers in GEMD objects.

* Attributes

  * :class:`~citrine.gemtables.variables.AttributeByTemplate`: for when the attribute occurs once per material history
  * :class:`~citrine.gemtables.variables.AttributeByTemplateAndObjectTemplate`: for when the attributes are distinguished by the object that they are contained in
  * :class:`~citrine.gemtables.variables.AttributeByTemplateAfterProcessTemplate`: for when measurements are distinguished by the process that precedes them
  * :class:`~citrine.gemtables.variables.AttributeInOutput`: for when attributes occur both in a process output and one or more of its inputs
  * :class:`~citrine.gemtables.variables.IngredientQuantityByProcessAndName`: for the specific case of the volume fraction, mass fraction, number fraction, or absolute quantity of an ingredient
  * :class:`~citrine.gemtables.variables.IngredientQuantityInOutput`: for the quantity of an ingredient between the root material and a given set of processes (useful for ingredients used in multiple processes)

* Identifiers

  * :class:`~citrine.gemtables.variables.RootInfo`: for fields defined on the material at the root of the Material History, like the name of the material
  * :class:`~citrine.gemtables.variables.RootIdentifier`: for the id of the Material History, which can be used as a unique identifier for the rows
  * :class:`~citrine.gemtables.variables.IngredientIdentifierByProcessTemplateAndName`: for the id of the material being used in an ingredient, which can be used as a key for looking up that input material
  * :class:`~citrine.gemtables.variables.IngredientIdentifierInOutput`: for the id of a material used in an ingredient between the root material and a given set of processes (useful for ingredients used in multiple processes)
  * :class:`~citrine.gemtables.variables.IngredientLabelByProcessAndName`: for a boolean that indicates whether an ingredient is assigned a given label

* Compound Variables

  * :class:`~citrine.gemtables.variables.XOR`: for combining multiple variable definitions into one variable, when only one of those definitions yields a result for a given tree (logical exclusive OR)

Available Column Definitions
----------------------------

There are several ways to define columns, depending on the type of the attribute that is being used as the data source for the column.

* Numeric attributes values, like :class:`~gemd.entity.value.continuous_value.ContinuousValue` and :class:`~gemd.entity.value.integer_value.IntegerValue`

 * :class:`~citrine.gemtables.columns.MeanColumn`: for the mean value of the numeric distribution
 * :class:`~citrine.gemtables.columns.StdDevColumn`: for the standard deviation of the numeric distribution, or empty if the value is *nominal*
 * :class:`~citrine.gemtables.columns.QuantileColumn`: for a user-defined quantile of the numeric distribution, or empty if the value is *nominal*
 * :class:`~citrine.gemtables.columns.OriginalUnitsColumn`: for getting the units, as entered by the data author, from the specific attribute value; valid for continuous values only

* Enumerated attribute values, like :class:`~gemd.entity.value.categorical_value.CategoricalValue`

 * :class:`~citrine.gemtables.columns.MostLikelyCategoryColumn`: for getting the mode
 * :class:`~citrine.gemtables.columns.MostLikelyProbabilityColumn`: for getting the probability of the mode

* Composition and chemical formula attribute values, like :class:`~gemd.entity.value.composition_value.CompositionValue`

 * :class:`~citrine.gemtables.columns.FlatCompositionColumn`: for flattening the composition into a chemical-formula-like string
 * :class:`~citrine.gemtables.columns.ComponentQuantityColumn`: for getting the (optionally normalized) quantity of a specific component, by name
 * :class:`~citrine.gemtables.columns.NthBiggestComponentNameColumn`: for getting the name of the n-th biggest component (by quantity)
 * :class:`~citrine.gemtables.columns.NthBiggestComponentQuantityColumn`: for getting the (optionally normalized) quantity of the n-th biggest component (by quantity)

* Molecular structure attribute values, like :class:`~gemd.entity.value.molecular_value.MolecularValue`

 * :class:`~citrine.gemtables.columns.MolecularStructureColumn`: for getting molecular structures in a line notation

* String and boolean valued fields, like identifiers and non-attribute fields

 * :class:`~citrine.gemtables.columns.IdentityColumn`: for simply casting the value to a string, which doesn't work on values from Attributes
