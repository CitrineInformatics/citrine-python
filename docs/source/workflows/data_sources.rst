.. _data-sources:

Data Sources
============

Data sources are used by modules to pull data from outside of the AI engine.
For example, a :doc:`predictor <predictors>` may need to define external training data.

GEM Table Data Source
---------------------

An :class:`~citrine.informatics.data_sources.GemTableDataSource` references a GEM Table.
As explained more in the :doc:`documentation <../data_extraction>`, GEM Tables provide a structured version of on-platform data.
GEM Tables are specified by the display table uuid, version number, and optional formulation descriptor.
A formulation descriptor must be specified if formulations should be built from the data source.
If specified, any formulations emitted by the data source are stored using the provided descriptor.
The example below assumes that the uuid and the version of the desired GEM Table are known.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.predictors import AutoMLPredictor, GraphPredictor
    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, ChemicalFormulaDescriptor

    data_source = GemTableDataSource(
        table_id = "842434fd-11fe-4324-815c-7db93c7ed81e",
        table_version = "2"
    )

    auto_ml_predictor = AutoMLPredictor(
        name = "Band gap predictor",
        description = "Predict the band gap from the chemical formula and crystallinity",
        inputs = [
            ChemicalFormulaDescriptor("terminal~formula"),
            CategoricalDescriptor("terminal~crystallinity", categories=[
                "Single crystalline", "Amorphous", "Polycrystalline"])
        ],
        outputs = [RealDescriptor("terminal~band gap", lower_bound=0, upper_bound=20, units="eV")]
    )

    predictor = GraphPredictor(
        name = "Root predictor",
        predictors = [auto_ml_predictor],
        training_data = [data_source]
    )
        

Note that the descriptor keys above are the headers of the *variable* not the column in the table.
The last term in the column header is a suffix associated with the specific column definition rather than the variable.
It should be omitted from the descriptor key.
