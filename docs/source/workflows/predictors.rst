Predictors
==========

A predictor computes or predicts properties of materials.
The type of predictor defines how a property prediction is made.
Predictors must be registered to a project to be used in a :doc:`design workflow <design_workflows>`.

Simple ML predictor
-------------------

The :class:`~citrine.informatics.predictors.SimpleMLPredictor` predicts material properties using a machine-learned model.
Each predictor is defined by a set of inputs, outputs and latent variables.
Inputs are used as input features to the machine learning model.
Outputs are the properties that you would like the model to predict.
There must be at least one input and one output.
Latent variables are properties that you would like the model to predict and you think could also be useful in predicting the outputs.
If defined, latent variables are used to build hierarchical models.
One model is trained from inputs to latent variables, and another is trained from inputs and latent variables to outputs.
Thus, all inputs and latent variables are used to predict outputs.

Models are trained using data provided by the table associated with the ``training_data`` uid specified when creating a predictor.
The uid is a unique string associated with a table of existing data.

The following example demonstrates how to use the python SDK to create a :class:`~citrine.informatics.predictors.SimpleMLPredictor`, register the predictor to a project and wait for validation:

.. code:: python

   from time import sleep
   from citrine import Citrine
   from citrine.informatics.predictors import SimpleMLPredictor

   # create a session with citrine using your API key
   session = Citrine(api_key = API_KEY)

   # create project
   project = session.projects.register('Example project')

   # create SimpleMLPredictor (assumes descriptors for
   # inputs/outputs/latent variables have already been created)
   simple_ml_predictor = SimpleMLPredictor(
       name = 'Predictor name',
       description = 'Predictor description',
       inputs = [input_descriptor_1, input_descriptor_2],
       outputs = [output_descriptor_1, output_descriptor_2],
       latent_variables = [latent_variable_descriptor_1],
       training_data = training_data_table_uid  # string id for training data
   )

   # register predictor
   predictor = project.predictors.register(simple_ml_predictor)

   # wait until the predictor is no longer validating
   # we must get the predictor every time we wish to fetch the latest status
   while project.predictors.get(predictor.uid).status == "VALIDATING":
       sleep(10)

   # print final validation status
   validated_predictor = project.predictors.get(predictor.uid)
   print(validated_predictor.status)

   # status info will contain relevant validation information
   print(validated_predictor.status_info)

Graph predictor
---------------

The :class:`~citrine.informatics.predictors.GraphPredictor` stitches together multiple other predictors into a
directed bipartite graph, where every model node is connected to an arbitrary number of input descriptors and exactly
one output descriptor.

There are restrictions for a predictor to be used in a GraphPredictor:
- it must be registered and validated
- it must NOT be another GraphPredictor

The following example demonstrates how to use the python SDK to create a :class:`~citrine.informatics.predictors.GraphPredictor`.

.. code:: python

   from citrine.informatics.predictors import GraphPredictor

   # the other predictors have already been created and validated
   graph_predictor = GraphPredictor(
       name = 'Predictor name',
       description = 'Predictor description',
       predictors = [predictor1.uid, predictor2.uid, predictor3.uid]
   )

   # register predictor
   predictor = project.predictors.register(graph_predictor)