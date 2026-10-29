.. _data-sources:

Data Sources
============

Data sources are used by modules to pull data from outside of the AI engine.
For example, a :doc:`predictor <predictors>` may need to define external training data.

Snapshot Data Source
--------------------

A :class:`~citrine.informatics.data_sources.SnapshotDataSource` references a snapshot of on-platform data by its id.
Create the snapshot on the Citrine Platform, then copy its id.

.. code:: python

    from citrine.informatics.data_sources import SnapshotDataSource
    from citrine.informatics.predictors import AutoMLPredictor, GraphPredictor
    from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, ChemicalFormulaDescriptor

    data_source = SnapshotDataSource(snapshot_id="842434fd-11fe-4324-815c-7db93c7ed81e")

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
