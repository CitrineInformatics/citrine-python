.. data_extraction:

Data Extraction
===============

Ara is a component of the Citrine Platform data service that extracts data from GEMD's complex and expressive graphical representations into a tabular structure (like a CSV file) that is easier to consume in analytical contexts.
An Ara table is defined on a set of material histories, and the rows in the resulting Ara Table are in 1-to-1 correspondence with those material histories.
Columns correspond to data about the material histories, such as the temperature measured in a kiln used at a specific manufacturing step.

Defining row and columns
------------------------

A Row object describes a mapping from a list of datasets to rows of a table.
The only such mapping presently supported is :class:`~citrine.ara.rows.MaterialRunByTemplate`, which produces one row per Material Run associated with any of a list of material templates.

.. code-block:: python

   from citrine.ara.rows import MaterialRunByTemplate
   from taurus.entity.link_by_uid import LinkByUID
   row_def = MaterialRunByTemplate(
         templates=[LinkByUID(scope="templates", id="finished cookie")])

A :class:`~citrine.ara.variables.Variable` object specifies how to select a piece of data from each Material History.
Thus, it performs the first part of a mapping from the set of Material Histories to columns in the Ara table.

.. code-block:: python

   from citrine.ara.variables import AttributeByTemplate
   from taurus.entity.link_by_uid import LinkByUID
   final_density = AttributeByTemplateAfterProcessTemplate(
         name = "final density",
         attribute_template = LinkByUID(scope="templates", id="cookie density"),
         process_template = LinkByUID(scope="templates", id="apply glaze")

A :class:`~citrine.ara.columns.Column` object describes how to transform a Variable into a primitive value (e.g. a real number, an integer, or a string) that can be entered into a cell in a table.
This is necessary because GEMD Attributes are more general than primitive values; they often convey uncertainty estimates, for example.

.. code-block:: python

   from citrine.ara.columns import MeanColumn, StdColumn
   final_density_mean = MeanColumn(data_source="final density", target_units="g/cm^3")
   final_density_std = MeanColumn(data_source="final density", target_units="g/cm^3")

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

   defns = project.ara_definitions()
   preview = defns.preview(
         defn = ara_defn,
         preview_roots = [
               LinkByUID(scope="products", id="best cookie ever"),
               LinkByUID(scope="products", id="worst cookie ever")])
