Predictor Reports
=================

Training a predictor generally produces a set of inter-connected models.
A predictor report describes those models, for example their settings and what features are important to the model.
It does not include predictor evaluation metrics.
To learn more about predictor evaluation metrics, please see :doc:`PredictorEvaluationMetrics <predictor_evaluation_workflows>`.
The report can be accessed via ``predictor.report``.

A task to generate a predictor report is scheduled when a predictor is registered.
The report has a ``status`` and ``json`` member variables.
Status can be one of:

-  ``PENDING`` The report has been scheduled.
-  ``ERROR`` An error was thrown while generating the report.
-  ``OK`` The report was generated successfully and the results are ready.

Results of the report are in the ``descriptors`` and ``model_summaries`` attributes.
``descriptors`` is a list of :class:`~citrine.informatics.descriptors.Descriptor` objects that may be inputs or outputs to models in the predictor.

``model_summaries`` is a list of :class:`~citrine.informatics.reports.ModelSummary` objects, each one corresponding to a single model in the predictor.
Each ``ModelSummary`` includes the name of the model, a list of input descriptors, a list of output descriptors, the model's settings, and its feature importances.
``model_settings`` is a dictionary of settings and values, the details of which depend on the type of model.
One possible model settings dictionary is shown below:

.. code:: python

    {
        'Algorithm': 'Ensemble of non-linear estimators',
        'Number of estimators': 64,
        'Use jackknife': True
    }


``feature_importances`` is a list of :class:`~citrine.informatics.reports.FeatureImportanceReport` objects, each of which corresponds to a single output of the model.
It has fields ``output_key``, which is the key of the output descriptor, and ``importances``, which is a dictionary from input keys to their importance.
The input and output keys correspond to descriptors that can be found in the predictor report's ``descriptors`` field.
An example is shown below:

.. code:: python

    {
        'output_key': 'shear modulus',
        'importances': {
            'Young's modulus': 0.85,
            'Poisson's ratio': 0.15
        }
    }

For simple models, such as those that featurize inputs, the ``model_settings`` and ``feature_importances`` fields might be empty.

As an example, consider a :class:`~citrine.informatics.predictors.simple_ml_predictor.SimpleMLPredictor` with numeric inputs ``x`` and ``y`` and numeric output ``z``.
This predictor will produce a single model to predict ``z`` from ``x`` and ``y``.
In cases involving latent variables and/or input featurization, more models will be produced.
The code below shows how to create the predictor, register it, and view the report.
Assume that there is a training data table with known id and version.

.. code:: python

    from time import sleep

    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.descriptors import RealDescriptor
    from citrine.informatics.data_sources import GemTableDataSource

    # create input descriptors
    x = RealDescriptor('x', lower_bound=0, upper_bound=10, units='')
    y = RealDescriptor('y', lower_bound=0, upper_bound=10, units='')
    z = RealDescriptor('z', lower_bound=0, upper_bound=10, units='')

    # register a predictor with a project
    predictor = project.predictors.register(
       SimpleMLPredictor(
           name='ML predictor for z',
           description='Predicts z from x and y',
           inputs=[x, y],
           latent_variables=[],
           outputs=[z],
           training_data=[GemTableDataSource(
            table_id = training_table_id,
            table_version = training_table_version
           )]
       )
    )

    # wait for the predictor report to be ready
    while project.predictors.get(predictor.uid).report.status == 'PENDING':
       sleep(10)

    # print the json report
    report = project.predictors.get(predictor.uid).report
    print(report.json)
