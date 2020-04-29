Data Sources
=============

Data sources are used by modules to pull data from outside of the AI engine.
For example, a :doc:`predictor <predictors>` may need to define external training data.

CSV Data Source
----------------

The :class:`~citrine.informatics.data_sources.CSVDataSource` draws data from a CSV file stored on the data platform and annotates it by mapping each column name to a :class:`~citrine.informatics.descriptors.Descriptor`.
The file is referenced via a :class:`~citrine.resources.file_link.FileLink`.
Each FileLink references an explicit version of the CSV file.
Uploading a new file with the same name will produce a new version of the file with a new FileLink.

The columns in the CSV are extracted and parsed by a mapping of column header names to user-created descriptors.
Columns in the CSV that are not mapped with a descriptor are ignored.

The CSV must be UTF-8 encoded ASCII text with CRLF line terminators.
The best way to ensure this is to save the file in a "Comma Separated Values" format and not any of the other small CSV variations.
For example, Excel's default CSV format, "CSV UTF-8 (Comma Delimited)" is not parseable.

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

    data_source = CsvDataSource(
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
        training_data = data_source
    )

Ara Table Data Source
---------------

An :class:`~citrine.informatics.data_sources.AraTableDataSource` references an Ara table.
As explained more in the :doc:`documentation <../data_extraction>`, Ara tables provide a structured version of on-platform data.
Ara tables are specified by the display table uuid and version number.
The example below assumes that the uuid and the version of the desired Ara table are known.

.. code:: python

    from citrine.informatics.data_sources import AraTableDataSource
    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, ChemicalFormulaDescriptor

    data_source = AraTableDataSource(
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
        training_data = data_source
    )