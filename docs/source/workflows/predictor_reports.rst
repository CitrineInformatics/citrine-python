Predictor reports
=================

A predictor report describes the models in a predictor, for example, their settings and what features are important to the model.
It does not include performance metrics. To learn more about performance metrics, please see :doc:`PerformanceWorkflows <performance_workflows>`.
The report can be accessed via the python SDK via ``predictor.report``.

A task to generate a predictor report is scheduled when a predictor is registered.
The report has a ``status`` and ``json`` member variables.
Status can be one of:

-  ``PENDING`` The report has been scheduled.
-  ``ERROR`` An error was thrown while generating the report.
-  ``OK`` The report was generated successfully and the results are ready.

Results of the report are stored as a dictionary in the ``json`` member variable.
This dictionary contains two keys: ``models`` and ``descriptors``.
``descriptors`` is a list of dictionaries, each one a serialized copy of a descriptor that is involved in the predictor.
Their structure depends on the descriptor type, but all descriptors have a ``descriptor_key`` field.

``models`` is a list of dictionaries, each one containing information about a model that is involved in the predictor.
Different predictors produce different types of models, and different models have different kinds of information.
But in general, for each model there are the following keys: ``name``, ``display_name``, ``type``, ``inputs``, ``outputs``, ``model_settings``, and ``feature_importances``.
``inputs`` and ``outputs`` are lists of strings, each one corresponding to the ``descriptor_key`` of a descriptor that is present in the ``descriptors`` field.
``model_settings`` is a nested set of properties, the details of which depend on the model in question.
``feature_importances`` is a list of dictionaries, each one of which corresponds to one of the model's outputs.
For each output there is a dictionary mapping each input to its importance for the model, which measures how strongly the model depends on that feature when making predictions.
These importances can be useful in gaining insight into how the machine learning model works.

For simple models, such as those that featurize inputs, the ``model_settings`` and ``feature_importances`` fields might be empty.

As an example, consider a :class:`~citrine.informatics.predictors.SimpleMLPredictor` with numeric inputs ``x`` and ``y`` and numeric output ``z``.
This predictor will produce a single model to predict ``z`` from ``x`` and ``y``, although in cases involving latent variables and/or input featurization, more models will be produced.
The code below shows how to create the predictor, register it, and view the report.
Assume that there is a training data table with known id and version.

.. code:: python

    from time import sleep

    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.descriptors import RealDescriptor
    from citrine.informatics.data_sources import AraTableDataSource

    # create input descriptors
    x = RealDescriptor('x', lower_bound=0, upper_bound=10)
    y = RealDescriptor('y', lower_bound=0, upper_bound=10)
    z = RealDescriptor('z', lower_bound=0, upper_bound=10)

    # register a predictor with a project
    predictor = project.predictors.register(
       SimpleMLPredictor(
           name='ML predictor for z',
           description='Predicts z from x and y',
           inputs=[x, y],
           latent_variables=[],
           outputs=[z],
           training_data=AraTableDataSource(
            table_id = training_table_id,
            table_version = training_table_version
           )
       )
    )

    # wait for the predictor report to be ready
    while project.predictors.get(predictor.uid).report.status == 'PENDING':
       sleep(10)

    # print the json report
    report = project.predictors.get(predictor.uid).report
    print(report.json)

For this example, the report would resemble the following.

.. code:: python

    {
        "models": [
            {
                "name": "GeneralLoloModel_1663408732",
                "type": "GeneralLoloModel",
                "display_name": "ML Model",
                "inputs": ["x", "y"],
                "outputs": ["z"],
                "model_settings": {
                    "name": "Algorithm",
                    "value": "Ensemble of non-linear estimators",
                    "children": [
                        {
                            "name": "Number of estimators",
                            "value": 64,
                            "children": []
                        },
                        {
                            "name": "Minimum samples per leaf",
                            "value": 1,
                            "children": []
                        },
                        {
                            "name": "Maximum tree depth",
                            "value": 30,
                            "children": []
                        }
                    ]
                },
                "feature_importances": [
                    {
                        "response_key": "z",
                        "importances": {
                            "x": 0.8,
                            "y": 0.2
                        }
                    }
                ]
            }
        ],
        "descriptors": [
            {
                "descriptor_key": "x",
                "lower_bound": 0,
                "upper_bound": 10,
                "units": "",
                "category": "Real"
            },
            {
                "descriptor_key": "y",
                "lower_bound": 0,
                "upper_bound": 10,
                "units": "",
                "category": "Real"
            },
            {
                "descriptor_key": "z",
                "lower_bound": 0,
                "upper_bound": 10,
                "units": "",
                "category": "Real"
            }
        ]
    }
