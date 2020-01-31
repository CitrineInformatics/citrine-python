.. _extraction:

Data Extraction
===============

Ara is a component of the Citrine Platform data service that extracts data from GEMD's complex and expressive graphical representations into a tabular structure (like a CSV file) that is easier to consume in analytical contexts.  The rows in the resulting Ara Table are in 1-to-1 correspondence with the set of material histories.  Columns correspond to data about the material histories, such as the temperature measured in a kiln used at a specific manufacturing step.

Row
---

A Row object describes a mapping from a dataset to rows of a table. The only such mapping presently supported is :class:`citrine.informatics.ara.MaterialRunByTemplate`, which produces one row per Material Run associated with any of a list of material templates.

Variable
--------

A :class:`citrine.informatics.ara.Variable` object specifies how to select a piece of data from each Material History. Thus, it serves as a mapping from the set of Material Histories to a column in the Ara table.

Ara Definition
--------------

The :ref:`AraDefinition` object defines how to build an Ara Table. It specifies a list of UUIDs for datasets to query in generating the table, a list of :class:`citrine.informatics.ara.Row` objects that define material histories to use as rows, and a list of :class:`citrine.informatics.ara.Variable` objects that specify how to extract data from those material histories into columns.

AraDefinitionCollection
-----------------------

An :ref:`AraDefinitionCollection` object facilitates access to the collection of all Ara definitions associated with a Project. Via such an object, one can preview an AraDefinition on an explicit set of roots.

For example:
[Placeholder]

Reading tables
--------------
[Placeholder]
