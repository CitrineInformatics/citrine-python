.. data_extraction:

[ALPHA] Data Extraction
=========================

Ara is a component of the Citrine Platform data service that extracts data from GEMD's complex and expressive graphical representations into a tabular structure (like a CSV file) that is easier to consume in analytical contexts.
An Ara table is defined on a set of material histories, and the rows in the resulting Ara Table are in 1-to-1 correspondence with those material histories.
Columns correspond to data about the material histories, such as the temperature measured in a kiln used at a specific manufacturing step.

Defining row and columns
------------------------

A Row object describes a mapping from a list of datasets to rows of a table by selecting a set of Material Histories.
Each Material History corresponds to exactly one row, though the Material Histories may overlap such that the same objects contribute data to multiple rows.
For example, the material histories of distinct Material Runs will map to exactly two rows even if their histories are identical up to differing Process Runs of their final baking step.
The only way to define rows right now is through :class:`~citrine.ara.rows.MaterialRunByTemplate`, which produces one row per Material Run associated with any of a list of material templates.

.. code-block:: python

   from citrine.ara.rows import MaterialRunByTemplate
   from taurus.entity.link_by_uid import LinkByUID
   row_def = MaterialRunByTemplate(
         templates=[LinkByUID(scope="templates", id="finished cookie")])

A :class:`~citrine.ara.variables.Variable` object specifies how to select a piece of data from each Material History.
Thus, it performs the first part of a mapping from the set of Material Histories to columns in the Ara table.

.. code-block:: python

   from citrine.ara.variables import AttributeByTemplateAfterProcessTemplate
   from taurus.entity.link_by_uid import LinkByUID
   final_density = AttributeByTemplateAfterProcessTemplate(
         name = "final density",
         headers = ["Product", "Density"],
         attribute_template = LinkByUID(scope="templates", id="cookie density"),
         process_template = LinkByUID(scope="templates", id="apply glaze"))

A :class:`~citrine.ara.columns.Column` object describes how to transform a Variable into a primitive value (e.g. a real number, an integer, or a string) that can be entered into a cell in a table.
This is necessary because GEMD Attributes are more general than primitive values; they often convey uncertainty estimates, for example.

.. code-block:: python

   from citrine.ara.columns import MeanColumn, StdDevColumn
   final_density_mean = MeanColumn(data_source="final density", target_units="g/cm^3")
   final_density_std = StdDevColumn(data_source="final density", target_units="g/cm^3")

The data_source parameter is a reference to a Variable for this Column to describe, so the value of data_source must match the name of a Variable.

Defining tables
---------------

The :class:`~citrine.resources.ara_definition.AraDefinition` object defines how to build an Ara Table.
It specifies a list of UUIDs for datasets to query in generating the table,
a list of :class:`~citrine.ara.rows.Row` objects that define material histories to use as rows,
a list of :class:`~citrine.ara.variables.Variable` objects that specify how to extract data from those material histories,
and a list of :class:`~citrine.ara.columns.Column` objects to transform those variables into columns.

.. code-block:: python

   from citrine.resources.ara_definition import AraDefinition
   from citrine._serialization.properties import UUID
   ara_defn = AraDefinition(
         name = "cookies",
         description = "Cookie densities",
         datasets = [UUID("7d040451-7cfb-45ca-9e0e-4b2b7010edd6")],
         variables = [final_density],
         rows = [row_def],
         columns = [final_density_mean, final_density_std])

Creating and reading tables
---------------------------

Calling :func:`~citrine.resources.project.Project.ara_definitions` on a project returns an :class:`~citrine.resources.ara_definition.AraDefinitionCollection` object, which facilitates access to the collection of all Ara definitions visible to a Project.
Via such an object, one can preview a draft AraDefinition on an explicit set of Material Histories, defined by their root materials:

For example:

.. code-block:: python

   defns = project.ara_definitions
   preview = defns.preview(
         defn = ara_defn,
         preview_roots = [
               LinkByUID(scope="products", id="best cookie ever"),
               LinkByUID(scope="products", id="worst cookie ever")])

Available Row Definitions
------------------------------

Currently, Ara provides only a single way to define Rows: by the :class:`~taurus.entity.templates.MaterialTemplate` of the roots of the material histories that correspond to each row.

:class:`~citrine.ara.rows.MaterialRunByTemplate`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~citrine.ara.rows.MaterialRunByTemplate` class defines Rows through a list of :class:`~taurus.entity.templates.MaterialTemplate`.
Every :class:`~taurus.entity.object.MaterialRun` that is assigned to any template in the list is used as the root of a  Material History to be mapped to a Row.
This is helpful when the rows correspond to classes of materials that are defined through their templates.
For example, there could be a :class:`~taurus.entity.templates.MaterialTemplate` called "Cake" that is used in all
of the cakes and another called "Brownies" that is used in all of the brownies.
By including one or both of those templates, you can define a table of Cakes, Brownies, or both.

Available Variable Definitions
------------------------------------------

There are several ways to define variables that take their values from Attributes and fields in GEMD objects.

* Attributes

  * :class:`~citrine.ara.variables.AttributeByTemplate`: for when the attribute occurs once per material history
  * :class:`~citrine.ara.variables.AttributeByTemplateAndObjectTemplate`: for when the attributes are distinguished by the object that they are contained in
  * :class:`~citrine.ara.variables.AttributeByTemplateAfterProcess`: for when measurements are distinguished by the process that precedes them
  * :class:`~citrine.ara.variables.IngredientQuantityByProcessAndName`: for the specific case of the volume fraction, mass fraction, number fraction, or absolute quantity of an ingredient

* Fields

  * :class:`~citrine.ara.variables.RootInfo`: for fields defined on the material at the root of the Material History, like the name of the material
  * :class:`~citrine.ara.variables.RootIdentifier`: for the id of the Material History, which can be used as a unique identifier for the rows
  * :class:`~citrine.ara.variables.IngredientIdentifierByProcessTemplateAndName`: for the id of the material being used in an ingredient, which can be used as a key for looking up that input material
  * :class:`~citrine.ara.variables.IngredientLabelByProcessAndName`: for a boolean that indicates whether an ingredient is assigned a given label

Available Column Definitions
-----------------------------------------------

There are several ways to define columns, depending on the type of the attribute that is being used as the data source for the column.

* Numeric attributes values, like :class:`~taurus.entity.continuous_value.ContinuousValue` and :class:`~taurus.entity.integer_value.IntegerValue`

 * :class:`~citrine.ara.columns.MeanColumn`: for the mean value of the numeric distribution
 * :class:`~citrine.ara.columns.StdDevColumn`: for the standard deviation of the numeric distribution, or empty if the value is *nominal*
 * :class:`~citrine.ara.columns.QuantileColumn`: for a user-defined quantile of the numeric distribution, or empty if the value is *nominal*
 * :class:`~citrine.ara.columns.OriginalUnitsColumn`: for getting the units, as entered by the data author, from the specific attribute value; valid for continuous values only

* Enumerated values, like :class:`~taurus.entity.categorical_value.CategoricalValue`

 * :class:`~citrine.ara.columns.MostLikelyCategoryColumn`: for getting the mode
 * :class:`~citrine.ara.columns.MostLikelyProbabilityColumn`: for getting the probability of the mode

* String and boolean valued fields

 * :class:`~citrine.ara.columns.IdentityColumn`: for simply casting the value to a string, which doesn't work on values from attributes
