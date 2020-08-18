Data Sources
============

Data sources are used by modules to pull data from outside of the AI engine.
For example, a :doc:`predictor <predictors>` may need to define external training data.

CSV Data Source
---------------

The :class:`~citrine.informatics.data_sources.CSVDataSource` draws data from a CSV file stored on the data platform and annotates it by mapping each column name to a :class:`~citrine.informatics.descriptors.Descriptor`.
The file is referenced via a :class:`~citrine.resources.file_link.FileLink`.
Each FileLink references an explicit version of the CSV file.
Uploading a new file with the same name will produce a new version of the file with a new FileLink.

The columns in the CSV are extracted and parsed by a mapping of column header names to user-created descriptors.
Columns in the CSV that are not mapped with a descriptor are ignored.

Assume that a file data.csv exists with the following contents:

.. code::

    Chemical Formula,Gap,Crystallinity
    Bi2Te3,0.153,Single crystalline
    Mg2Ge,0.567,Single crystalline
    GeTe,0.7,Amorphous
    Sb2Se3,1.15,Polycrystalline

That file could be used as the training data for a predictor as:

.. code:: python

    from citrine.informatics.data_sources import CSVDataSource
    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, ChemicalFormulaDescriptor

    file_link = dataset.files.upload("./data.csv", "bandgap_data.csv")

    data_source = CSVDataSource(
        file_link = file_link,
        # `column_definitions` maps a column header to a descriptor
        # the column header and the descriptor key do not need to be identical
        column_definitions = {
            "Chemical Formula": ChemicalFormulaDescriptor("formula"),
            "Gap": RealDescriptor("Band gap", lower_bound=0, upper_bound=20, units="eV"),
            "Crystallinity": CategoricalDescriptor("Crystallinity", categories=[
                "Single crystalline", "Amorphous", "Polycrystalline"])
        }
    )

    predictor = SimpleMLPredictor(
        name = "Band gap predictor",
        description = "Predict the band gap from the chemical formula and crystallinity",
        inputs = [
            # referencing `data_source.column_definitions` is one way to ensure that the
            # descriptors in the training data match the descriptors in the predictor definition
            data_source.column_definitions["Chemical Formula"],
            data_source.column_definitions["Crystallinity"]
        ],
        outputs = [data_source.column_definitions["Gap"]],
        latent_variables = [],
        training_data = [data_source]
    )

An optional list of identifiers can be specified.
Identifiers uniquely identify a row and are used in the context of simple mixtures to link from an ingredient to the its properties.
Each identifier must correspond to a column header name.
No two rows within this column can contain the same value.
If a column should be parsed as data and used as an identifier, identifier columns may overlap with the keys defined in the mapping from column header names to descriptors.

Identifiers are required in two circumstances.
These circumstances are only relevant if CSV data source represents simple mixture data.

1. Ingredient properties are featurized using a :class:`~citrine.informatics.predictors.GeneralizedMeanPropertyPredictor`.
   In this case, the link from identifier to row is used to compute mean ingredient property values.
2. Simple mixtures that contain mixtures are simplified to recipes that contain only leaf ingredients using a :class:`~citrine.informatics.predictors.SimpleMixturePredictor`.
   In this case, links from each mixture's ingredients to its row (which may also be a mixture) are used to recursively crawl hierarchical blends of blends and construct a recipe that contains only leaf ingredients.

Note: to build a formulation from a CSV data source an :class:`~citrine.informatics.predictors.IngredientsToSimpleMixturePredictor` must be present in the workflow.
Additionally, each ingredient id used as a key in the predictor's map from ingredient id to its quantity must exist in an identifier column.

As an example, consider the following saline solution data.

+-------------------+----------------+---------------+---------+
| Ingredient id     | water quantity | salt quantity | density |
+===================+================+===============+=========+
| hypertonic saline | 0.93           | 0.07          | 1.08    |
+-------------------+----------------+---------------+---------+
| isotonic saline   | 0.99           | 0.01          | 1.01    |
+-------------------+----------------+---------------+---------+
| water             |                |               | 1.0     |
+-------------------+----------------+---------------+---------+
| salt              |                |               | 2.16    |
+-------------------+----------------+---------------+---------+

Hypertonic and isotonic saline are mixtures formed by mixing water and salt.
Ingredient identifiers are given by the first column.
A CSV data source and :class:`~citrine.informatics.predictors.IngredientsToSimpleMixturePredictor` can be configured to construct simple mixtures from this data via the following:

.. code:: python

    from citrine.informatics.data_sources import CSVDataSource
    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    from citrine.informatics.predictors import IngredientsToSimpleMixturePredictor

    file_link = dataset.files.upload("./saline_solutions.csv", "saline_solutions.csv")

    # create descriptors for each ingredient quantity
    water_quantity = RealDescriptor('water quantity', 0, 1)
    salt_quantity = RealDescriptor('salt quantity', 0, 1)

    # create a descriptor to hold density data
    density = RealDescriptor('density', lower_bound=0, upper_bound=1000, units='g/cc')

    data_source = CSVDataSource(
        file_link = file_link,
        column_definitions = {
            'water quantity': water_quantity,
            'salt quantity': salt_quantity,
            'density': density
        },
        identifiers=['Ingredient id']
    )

    # create a descriptor to hold simple mixtures
    formulation = FormulationDescriptor('simple mixture')

    IngredientsToSimpleMixturePredictor(
        name='Ingredients to simple mixture predictor',
        description='Constructs a mixture from ingredient quantities',
        output=formulation,
        # map from ingredient id to its quantity
        id_to_quantity={
            'water': water_quantity,
            'salt': salt_quantity
        },
        # label water as a solvent and salt a solute
        labels={
            'solvent': ['water'],
            'solute': ['salt']
        }
    )

GEM Table Data Source
---------------------

An :class:`~citrine.informatics.data_sources.GemTableDataSource` references a GEM Table.
As explained more in the :doc:`documentation <../data_extraction>`, GEM Tables provide a structured version of on-platform data.
GEM Tables are specified by the display table uuid, version number and optional formulation descriptor.
A formulation descriptor must be specified if formulations should be built from the data source.
If specified, any formulations emitted by the data source are stored using the provided descriptor.
The example below assumes that the uuid and the version of the desired GEM Table are known.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, ChemicalFormulaDescriptor

    data_source = GemTableDataSource(
        table_id = "842434fd-11fe-4324-815c-7db93c7ed81e",
        table_version = "2"
    )

    predictor = SimpleMLPredictor(
        name = "Band gap predictor",
        description = "Predict the band gap from the chemical formula and crystallinity",
        inputs = [
            ChemicalFormulaDescriptor("root~formula"),
            CategoricalDescriptor("root~crystallinity", categories=[
                "Single crystalline", "Amorphous", "Polycrystalline"])
        ],
        outputs = [RealDescriptor("root~band gap", lower_bound=0, upper_bound=20, units="eV")],
        latent_variables = [],
        training_data = [data_source]
    )

Note that the descriptor keys above are the headers of the *variable* not the column in the table.
The last term in the column header is a suffix associated with the specific column definition rather than the variable.
It should be omitted from the descriptor key.
