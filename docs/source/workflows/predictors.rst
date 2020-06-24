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

Ingredients to simple mixture predictor
---------------------------------------

The :class:`~citrine.informatics.predictors.IngredientsToSimpleMixturePredictor` constructs a simple mixture from a list of ingredients.
Ingredients are specified by a map from ingredient id to the descriptor that contains the ingredient's quantity.
For example, ``{'water': RealDescriptor('water quantity', 0, 1}`` defines an ingredient ``water`` with quantity held by the descriptor ``water quantity``.
There must be a corresponding (id, quantity) pair in the map for all possible ingredients.
If a material does not contain data for a given quantity descriptor key it is assumed that ingredient is not present in the mixture.

Let's add another ingredient ``salt`` to our map and say we are given data in the form:

+-------------------+----------------+---------------+----------------+
| Ingredient id     | water quantity | salt quantity | density (g/cc) |
+===================+================+===============+================+
| hypertonic saline | 0.93           | 0.07          | 1.08           |
+-------------------+----------------+---------------+----------------+
| isotonic saline   | 0.99           | 0.01          | 1.01           |
+-------------------+----------------+---------------+----------------+
| water             |                |               | 1.0            |
+-------------------+----------------+---------------+----------------+
| salt              |                |               | 2.16           |
+-------------------+----------------+---------------+----------------+

There are two mixtures, hypertonic and isotonic saline formed by mixing water and salt together in different amounts.
(Note, water and salt are leaf ingredients; and, hence these rows do not contain quantity data.)
Mixtures are defined by a map from ingredient id to quantity, so this predictor would form 2 mixtures with recipes:

.. code:: python

    # hypertonic saline
    {'water': 0.93, 'salt': 0.07}

    # isotonic saline
    {'water': 0.99, 'salt': 0.01}

Ingredients may be given 0 or more labels.
Labels provide a way to group or distinguish one or more ingredients and can be used to featurize mixtures (discussed in the next section).
The same label may be given to multiple ingredients, and a single ingredient may be given multiple labels.
Labels are specified using a map from each label to a list of all ingredients that should be given that label.
Anytime a recipe contains a non-zero amount of labeled ingredient, the ingredient is assigned the label.
For example, we may wish to label ``water`` as a solute and ``salt`` as a solvent.
These labels are specified via:

.. code:: python

    labels = {'solvent': ['water'], 'solute': ['salt']}

The following example illustrates how an :class:`~citrine.informatics.predictors.IngredientsToSimpleMixturePredictor` is constructed for the saline example.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    from citrine.informatics.predictors import IngredientsToSimpleMixturePredictor

    # create a descriptor to hold simple mixtures
    formulation = FormulationDescriptor('simple mixture')

    # create descriptors for each ingredient quantity
    water_quantity = RealDescriptor('water quantity', 0, 1)
    salt_quantity = RealDescriptor('salt quantity', 0, 1)

    # table with simple mixtures and their ingredients
    data_source = AraTableDataSource(table_uid, 0)

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
        },
        training_data=data_source
    )

Simple mixture predictor
------------------------

Simple mixtures may contain ingredients that are blends of other simple mixtures.
Along the lines of the example above, hypertonic saline can be mixed with water to form isotonic saline.
Often, the properties of a hierarchical mixture are strongly associated with its leaf ingredients.
The :class:`~citrine.informatics.predictors.SimpleMixturePredictor` flattens a hierarchical recipe into a recipe that contains only those leaf ingredients.

The formulation to be flattened is specified by an ``input_descriptor`` formulation descriptor; the associated material history of the input formulation is traversed to determine the leaf ingredients.
These leaf ingredients are then summed across all leaves of the mixing processes, with the resulting candidates described by an ``output_descriptor`` formulation descriptor.
The ``training_data`` parameter is used as a source of formulation recipes to be used in flattening hierarchical simple mixtures.

The following example illustrates how a :class:`~citrine.informatics.predictors.SimpleMixturePredictor` can be used to flatten the ingredients used in aqueous dilutions of hypertonic saline, yielding just the quantities of the leaf constituents salt and water.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor
    from citrine.informatics.predictors import SimpleMixturePredictor

    input_formulation = FormulationDescriptor('diluted saline')
    output_formulation = FormulationDescriptor('diluted saline (flattened)')

    # table with simple mixtures and their ingredients
    data_source = AraTableDataSource(table_uid, 0)

    SimpleMixturePredictor(
        name='Simple mixture predictor',
        description='Constructs a formulation descriptor that flattens a hierarchy of simple mixtures into the quantities of leaf ingredients',
        input_descriptor=input_formulation,
        output_descriptor=output_formulation,
        training_data=data_source
    )

Generalized mean property predictor
-----------------------------------

Often, properties of a mixture are proportional to the properties of it's ingredients.
For example, the density of a saline solution can be computed from the densities of water and salt multiplied by their respective amounts:

.. math::

    d_{saline} = d_{water} * f_{water} + d_{salt} * f_{salt}

where :math:`d` is density and :math:`f` is relative ingredient fraction.
If the densities of water and salt are known, we can compute the expected density of a candidate mixture using this predictor.

The :class:`~citrine.informatics.predictors.GeneralizedMeanPropertyPredictor` computes mean properties of simple mixture ingredients.
To configure a mean property predictor, we must specify:

- an input descriptor that holds the mixture's recipe and ingredient labels
- a list of properties to featurize
- the power of the `generalized mean <https://en.wikipedia.org/wiki/Generalized_mean>`_
  (A power of 1 is equivalent to the arithmetic mean, and a power 2 is equivalent to the root mean square.)
- a data source that contains all ingredients and their properties
- how to handle missing ingredient properties

An optional label may also be specified if the mean should only be computed over ingredients given a specific label.

Missing ingredient properties can be handled one of three ways:

1. If ``impute_properties == False``, an error will be thrown if an ingredient is missing a featurized property.
   Use this option if you expect ingredient properties to be dense (always present) and would like to be notified when properties are missing.
2. If ``impute_properties == True`` and no ``default_properties`` are specified, missing properties will be filled in using the average value across the entire dataset.
   The average is computed from any row with data corresponding to the missing property, regardless of label or material type (i.e. the average is computed from all leaf ingredients and mixtures).
3. If ``impute_properties == True`` and ``default_properties`` are specified, the specified property value will be used when an ingredient property is missing (instead of the average over the dataset).
   This allows complete control over what values are imputed.
   Default properties cannot be specified if ``impute_properties == False`` (because missing properties are not filled in).

For example, say we add boric acid (a common antiseptic) as a possible ingredient to a saline solution but do not know its density.
Our leaf ingredient data might resemble:

+---------------+----------------+
| Ingredient id | Density (g/cc) |
+===============+================+
| water         | 1.0            |
+---------------+----------------+
| salt          | 2.16           |
+---------------+----------------+
| boric acid    | N/A            |
+---------------+----------------+

If ``impute_properties == False``, an error will be thrown every time a mixture that includes boric acid is encountered.
If ``impute_properties == True`` and no ``default_properties`` are specified, an density of :math:`\left( 1.0 + 2.16 \right) / 2 = 1.58` will be used.
If a value other than 1.58 should be used, e.g. 2.0, this can be specified by setting ``default_properties = {'density': 2.0}``.

The example below show how to configure a mean property predictor to compute mean solute density in simple mixtures.

.. code:: python

    from citrine.informatics.data_sources import AraTableDataSource
    from citrine.informatics.descriptors import FormulationDescriptor
    from citrine.informatics.predictors import GeneralizedMeanPropertyPredictor

    # descriptor that holds simple mixture data
    formulation = FormulationDescriptor('simple mixture')

    # table with simple mixtures and their ingredients
    data_source = AraTableDataSource(table_uid, 0)

    GeneralizedMeanPropertyPredictor(
        name='Mean property predictor',
        description='Computes 1-mean ingredient properties',
        input_descriptor=formulation,
        # featurize ingredient density
        properties=['density'],
        # compute the 1-mean
        p=1,
        training_data=data_source,
        # impute ingredient properties, if missing
        impute_properties=True,
        # if missing, use with 2.0
        default_properties={'density': 2.0},
        # only featurize ingredients labeled as a solute
        label='solute'
    )

Ingredient Fractions Predictor
------------------------------

The :class:`~citrine.informatics.predictors.IngredientFractionsPredictor` featurizes ingredient fractions in a simple mixture.
The predictor is configured by specifying a descriptor that contains simple mixture data and a list of known ingredients to featurize.
The list of ingredients should be the list of all possible ingredients for the input mixture.
If the mixture contains an ingredient that wasn't specified when the predictor was created, an error will be thrown.

For each featurized ingredient, the predictor will inspect the recipe and compute a response equal to the ingredient's total fraction in the recipe.
If an ingredient is not present in the mixture's recipe, the response for that ingredient fraction will be 0.
For example, given a recipe ``{'water': 0.9, 'salt': 0.1}`` and featurized ingredients ``['water', 'salt', 'boric acid']``,
this predictor would compute outputs:

- ``water share in simple mixture == 0.9``
- ``salt share in simple mixture == 0.1``
- ``boric acid share in simple mixture == 0.0``

The example below shows how to configure an ``IngredientFractionsPredictor`` that computes these responses.

.. code:: python

    from citrine.informatics.predictors import IngredientFractionsPredictor
    from citrine.informatics.descriptors import FormulationDescriptor

    IngredientFractionsPredictor(
        name='Ingredient Fractions Predictor',
        description='Computes fractions of provided ingredients',
        input_descriptor=FormulationDescriptor('simple mixture')
        ingredients=['water', 'salt', 'boric acid']
    )

Label fractions predictor
-------------------------

The :class:`~citrine.informatics.predictors.LabelFractionsPredictor` computes total fraction of ingredients with a given label.
The predictor is configured by specifying a formulation descriptor that holds simple mixture data (i.e. recipes and ingredient labels) and a list of labels to featurize.
A separate response is computed for each featurized label by summing all quantities in the recipe associated with ingredients given the label.

The following example demonstrates how to create a predictor that computes the total fractions of solute and solvent in a simple mixture.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor
    # descriptor that holds simple mixture data
    formulation = FormulationDescriptor('simple mixture')

    label_fractions = LabelFractionsPredictor(
        name='Saline solution label fractions',
        description='Computes total fraction of solute and solvent',
        input_descriptor=formulation,
        labels=['solute', 'solvent']
    )

Predictor Reports
-----------------

A :doc:`predictor report <predictor_reports>` describes a machine-learned model, for example its settings and what features are important to the model. 
It does not include performance metrics. To learn more about performance metrics, please see :doc:`PerformanceWorkflows <performance_workflows>`.

Data Sources
-------------

A :doc:`data source <data_sources>` references the training data used by a predictor.

Example: preprocessing and postprocessing in a GraphPredictor
-------------------------------------------------------------

Within a :class:`~citrine.informatics.predictors.GraphPredictor`, one can use :class:`~citrine.informatics.predictors.ExpressionPredictor` modules to preprocess data before performing machine learning with a :class:`~citrine.informatics.predictors.SimpleMLPredictor`, and to post-process the SimpleMLPredictor's output.
This is a very common and powerful use case for graphical modeling.
Here we show an example of how to combine these modules to accomplish those many suitable tasks.

Using ExpressionPredictors to perform pre-processing can be used to featurize data, which is a valuable way to leverage domain knowledge by transforming raw inputs into quantities known to be relevant.
In the example below, we use an ExpressionPredictor to annotate the training data with a "hydration ratio".
The hydration ratio is the mass ratio of water to flour.
Bakers know this quantity to be of fundamental importance to the taste and texture of bread, so computing this quantity might be expected to help the SimpleMLPredictor make more efficient use of scarce training data.
(In a more standard materials science context, an ExpressionPredictor might be used to annotate semiconductor data with an analytical expression of idealized electron mobility as a function of dopant concentrations.)

In the example below, we use the ExpressionPredictor feature to compute a bread loaf product's shelf life.
This simulates a scenario where shelf life is determined by a quality control rule of a few physically measurable quantities: ``final pH`` and ``final hydration`` as estimated by the SimpleMLPredictor, as well as the fraction of salt in the ingredients.
Using ExpressionPredictors in this manner to post-process learned data is often useful for displaying information on the platform based on transformations of the learned physical properties.
This pattern is also extremely useful for performing optimization over complex objectives: in the following example, we can use shelf life as an objective or constraint in a :doc:`DesignWorkflows <design_workflows>`.

.. code:: python

    from citrine.informatics.descriptors import RealDescriptor
    from citrine.informatics.predictors import (
        ExpressionPredictor,
        GraphPredictor,
        SimpleMLPredictor
    )

    ######## Omitted step: create DataSource with columns associated with the following descriptors ########
    # wheat_flour_quantity = RealDescriptor(
    #     'wheat flour mass', lower_bound=300, upper_bound=550, units="g")
    # rye_flour_quantity = RealDescriptor(
    #     'rye flour mass', lower_bound=0, upper_bound=100, units="g")
    # water_quantity = RealDescriptor(
    #    'water mass', lower_bound=200, upper_bound=400, units="g")
    # salt_quantity = RealDescriptor(
    #    'salt mass', lower_bound=4, upper_bound=8, units="g")
    # starter_quantity = RealDescriptor(
    #    'starter mass', lower_bound=5, upper_bound=30, units="g")
    # final_ph = RealDescriptor(
    #    'final pH', lower_bound=2.5, upper_bound=5, units="")
    # final_loaf_hydration = RealDescriptor(
    #    'final loaf hydration', lower_bound=0, upper_bound=100, units="")
    #
    # data_source = create_ara_data_source_from_breads_gemd(
    #    descriptors=[...descriptors above...])

    dough_hydration = RealDescriptor(
        'dough hydration', lower_bound=0, upper_bound=1)
    shelf_life = RealDescriptor(
        'approximate shelf life', lower_bound=0, upper_bound=72)

    dough_hydration_calculator = ExpressionPredictor(
        name = 'dough hydration calculator',
        expression = '(water + 0.5*starter) / (wheat + rye + 0.5*starter)',
        output = dough_hydration,
        aliases = {
            'wheat': 'wheat flour mass',
            'rye': 'rye flour mass',
            'water': 'water mass',
            'starter': 'starter mass'
        }
    )

    physical_properties_predictor = SimpleMLModel(
        name = 'physical properties model',
        inputs = [
            wheat_flour_quantity,
            rye_flour_quantity,
            water_quantity,
            salt_quantity,
            starter_quantity,
            dough_hydration
        ],
        outputs = [
            final_ph,
            final_loaf_hydration,
        ],
        training_data=training_table
    )

    shelf_life_calculator = ExpressionPredictor(
        name = 'shelf life estimator',
        expression = '4*exp(-0.1*pH - 1.3*w^2 + 5*(water+0.5*starter)/(wheat+rye+water+starter))',
        output = shelf_life,
        aliases = {
            'pH': 'final pH',
            'w': 'final loaf hydration',
            'wheat': 'wheat flour mass',
            'rye': 'rye flour mass',
            'water': 'water mass',
            'starter': 'starter mass'
        }
    )

    graph_predictor = GraphPredictor(
        name = 'bread shelf life predictor',
        description = 'Uses bread ingredients to estimate shelf life, given a fixed manufacturing process',
        predictors = [
            dough_hydration_calculator,
            physical_properties_predictor,
            shelf_life_calculator
        ]
    )

.. |Bread Predictor Graph Visualization| image:: bread_predictor_graph_viz.jpg
   :width: 800
   :alt: Visualization of graph predictor.

This example is shown below.
Nodes with dashed outlines represent degrees of freedom in the recipe, and those with solid outlines represent predictors.
Nodes with dotted outlines represent predicted quantities; note that only ``final pH`` and ``final loaf hydration`` are the only predicted quantities that exist in the training data.

|Bread Predictor Graph Visualization|
