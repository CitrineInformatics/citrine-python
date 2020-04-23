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

Models are trained using data provided by a :class:`~citrine.informatics.data_sources.DataSource` specified when creating a predictor.

The following example demonstrates how to use the python SDK to create a :class:`~citrine.informatics.predictors.SimpleMLPredictor`, register the predictor to a project and wait for validation:

.. code:: python

   from time import sleep
   from citrine import Citrine
   from citrine.informatics.predictors import SimpleMLPredictor
   from citrine.informatics.data_sources import AraTableDataSource

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
       training_data = AraTableDataSource(training_data_table_uid, 0)
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

Note, if multiple associated predictors use descriptors with the same key the output value with the least loss will be used.

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

Expression predictor
--------------------

The :class:`~citrine.informatics.predictors.ExpressionPredictor` defines an analytic (lossless) model that computes one real-valued output descriptor from one or more input descriptors.
An ExpressionPredictor should be used when the relationship between inputs and outputs is known.

A string is used to define the expression, and the corresponding output is defined by a :class:`~citrine.informatics.descriptors.RealDescriptor`.
The ``aliases`` parameter defines a mapping from expression arguments to descriptor keys.
Expression arguments with spaces are not supported, so an alias must be created for each input that has a space in its name.
Aliases are not required for inputs that do not contain spaces, but may be useful to avoid typing out the verbose descriptors in the expression string.
If an alias isn't defined, the expression argument is expected to match the descriptor key exactly.

The syntax is described in the `mXparser documentation <http://mathparser.org/mxparser-math-collection>`_.
Citrine-python currently supports the following operators and functions:
- basic operators: addition `+`, subtraction `-`, multiplication `*`, division `/`, exponentiation `^`
- built-in math functions:
  - trigonometric: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`
  - hyperbolic: `sinh`, `cosh`, `tanh`
  - logarithm: `log10`, `ln`
  - exponential: `exp`
- constants: `pi`, `e`

The following example demonstrates how to create an :class:`~citrine.informatics.predictors.ExpressionPredictor`.

.. code:: python

   from citrine.informatics.predictors import ExpressionPredictor

   shear_modulus = RealDescriptor('Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')

   shear_modulus_predictor = ExpressionPredictor(
       name = 'Shear modulus predictor',
       description = "Computes shear modulus from Young's modulus and Poisson's ratio.",
       expression = 'Y / (2 * (1 + v))',
       output = shear_modulus,
       aliases = {
           'Y': "Property~Young's modulus",
           'v': "Property~Poisson's ratio"
       }
   )

   # register predictor
   predictor = project.predictors.register(shear_modulus_predictor)

Predictor Reports
--------------------

A :doc:`predictor report <predictor_reports>` describes a machine-learned model, for example its settings and what features are important to the model. 
It does not include performance metrics. To learn more about performance metrics, please see :doc:`PerformanceWorkflows <performance_workflows>`.

Data Sources
-------------

A :doc:`data source <data_sources>` references the training data used by a predictor.
