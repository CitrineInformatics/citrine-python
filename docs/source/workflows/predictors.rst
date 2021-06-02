.. _predictors:

Predictors
==========

A predictor computes or predicts properties of materials.
All predictors take one or more :doc:`descriptors <descriptors>` as inputs and produce one or more output descriptors.
Types of predictors include machine learning models, featurizers, and analytic expressions.

A predictor must be registered to a project to be used in a :doc:`design workflow <design_workflows>`.


Auto ML predictor (ALPHA)
-------------------------

The :class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor` predicts material properties using a machine-learned model.
AutoMLPredictors allow you to use your domain knowledge to construct custom `GraphPredictors <#graph-predictor>`__ with fine grain control over the resulting graph.
Each AutoMLPredictor is defined by a set of inputs and an output.
Inputs are used as input features to the machine learning model.
The output is the property that you would like the model to predict.
There must be at least one input and only one output.
Unlike the `SimpleMLPredictor <#simple-ml-predictor>`__, only one model is trained from inputs to the output.

Models are trained using data provided by a :class:`~citrine.informatics.data_sources.DataSource` specified when creating a predictor.
The inputs and outputs are descriptors, which must correspond precisely to descriptors that exist in the training data or are produced by other predictors in the graphical model.
There are two important helper methods in this regard.
:func:`~citrine.resources.descriptors.DescriptorMethods.descriptors_from_data_source` can provide all of the descriptors that are present in the training data.
:func:`~citrine.resources.descriptors.DescriptorMethods.from_predictor_responses` can tell you what the outputs of a predictor will be, which is especially useful for featurizers.

The following example demonstrates how to use the python SDK to create an :class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor`, register the predictor to a project and wait for validation:

.. code:: python

   from citrine.informatics.predictors import AutoMLPredictor
   from citrine.seeding.find_or_create import create_or_update

   # create AutoMLPredictor (assumes descriptors for
   # inputs/output variables have already been created)
   auto_ml_predictor = AutoMLPredictor(
       name = 'Predictor name',
       description = 'Predictor description',
       inputs = [input_descriptor_1, input_descriptor_2],
       output = output_descriptor_1,
       training_data = [GemTableDataSource(training_data_table_uid, 1)]
   )

   predictor = create_or_update(collection=project.predictors,
                                resource=auto_ml_predictor
                               )


Graph predictor
---------------

The :class:`~citrine.informatics.predictors.graph_predictor.GraphPredictor` stitches together multiple other predictors into a
directed bipartite graph, where every model node is connected to an arbitrary number of input descriptors and exactly
one output descriptor.

Note, if multiple associated predictors use descriptors with the same key the output value with the least loss will be used.

There are restrictions for a predictor to be used in a GraphPredictor:
- it must be registered and validated
- it must NOT be another GraphPredictor

The following example demonstrates how to use the python SDK to create a :class:`~citrine.informatics.predictors.graph_predictor.GraphPredictor`.

.. code:: python

   from citrine.informatics.predictors import GraphPredictor
   from citrine.seeding.find_or_create import create_or_update

   # the other predictors have already been created and validated
   graph_predictor = GraphPredictor(
       name = 'Predictor name',
       description = 'Predictor description',
       predictors = [predictor1.uid, predictor2.uid, predictor3.uid],
       training_data = [GemTableDataSource(training_data_table_uid, 1)] # training data shared by all sub-predictors
   )

   # register or update predictor by name
   predictor = create_or_update(collection=project.predictors,
                                module=graph_predictor
                               )

For a more complete example of graph predictor usage, see :ref:`AI Engine Code Examples <graph_predictor_example>`.

.. _Expression Predictor:
Expression predictor
--------------------

The :class:`~citrine.informatics.predictors.expression_predictor.ExpressionPredictor` defines an analytic (lossless) model that computes one real-valued output descriptor from one or more input descriptors.
An :class:`~citrine.informatics.predictors.expression_predictor.ExpressionPredictor` should be used when the relationship between inputs and outputs is known.

A string is used to define the expression, and the corresponding output is defined by a :class:`~citrine.informatics.descriptors.RealDescriptor`.
An alias is required for each expression argument.
The ``aliases`` parameter defines a mapping from expression arguments to their associated input descriptors.
The expression argument does not need to match its descriptor key.
This is useful to avoid typing out the verbose descriptor keys in the expression string.
Note, spaces are not supported in expression arguments, e.g. ``Y`` is a valid argument while ``Young's modulus`` is not.

The syntax is described in the `mXparser documentation <http://mathparser.org/mxparser-math-collection>`_.
Citrine-python currently supports the following operators and functions:

- basic operators: addition ``+``, subtraction ``-``, multiplication ``*``, division ``/``, exponentiation ``^``
- built-in math functions:

  - trigonometric (input in radians): ``sin``, ``cos``, ``tan``, ``asin``, ``acos``, ``atan``
  - hyperbolic: ``sinh``, ``cosh``, ``tanh``
  - logarithm: ``log10``, ``ln``
  - exponential: ``exp``

- constants: ``pi``, ``e``

ExpressionPredictors do not support complex numbers.

The following example demonstrates how to create an :class:`~citrine.informatics.predictors.expression_predictor.ExpressionPredictor`.

.. code:: python

   from citrine.informatics.predictors import ExpressionPredictor

   youngs_modulus = RealDescriptor(key='Property~Young\'s modulus', lower_bound=0, upper_bound=100, units='GPa')
   poissons_ratio = RealDescriptor(key='Property~Poisson\'s ratio', lower_bound=-1, upper_bound=0.5, units='')
   shear_modulus = RealDescriptor(key='Property~Shear modulus', lower_bound=0, upper_bound=100, units='GPa')

   shear_modulus_predictor = ExpressionPredictor(
       name = 'Shear modulus predictor',
       description = "Computes shear modulus from Young's modulus and Poisson's ratio.",
       expression = 'Y / (2 * (1 + v))',
       output = shear_modulus,
       aliases = {
           'Y': youngs_modulus,
           'v': poissons_ratio
       }
   )

   # register or update predictor by name
   predictor = create_or_update(collection=project.predictors,
                                module=shear_modulus_predictor
                               )

For an example of expression predictors used in a graph predictor, see :ref:`AI Engine Code Examples <graph_predictor_example>`.

Molecular Structure Featurizer
------------------------------------
The :class:`~citrine.informatics.predictors.molecular_structure_featurizer.MolecularStructureFeaturizer`
computes a configurable set of features on molecular structure data, e.g. SMILES or InChI strings, using the `Chemistry Development Kit (CDK) <https://cdk.github.io/>`_.
The features are configured using the ``features`` and ``excludes`` arguments, which accept either feature names or predefined aliases.
The default is the `standard` alias, corresponding to eight features that are a good balance of cost and performance.

The feature names and descriptors are automatically constructed from the name of the input and the feature names.
The ``from_predictor_responses`` method will grab the descriptors for the features so that they can be fed into other predicors,
e.g., the :class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor`, as inputs.


The following example demonstrates how to use a :class:`~citrine.informatics.predictors.molecular_structure_featurizer.MolecularStructureFeaturizer` and
:class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor` to model a property of a molecule:

.. code:: python

    from citrine.informatics.descriptors import MolecularStructureDescriptor, RealDescriptor
    from citrine.informatics.predictors import MolecularStructureFeaturizer, AutoMLPredictor, GraphPredictor
    from citrine.seeding.find_or_create import create_or_update
    from citrine.informatics.data_sources import GemTableDataSource


    # descriptor for the molecular structure input
    input_desc = MolecularStructureDescriptor('Solvent SMILES')
    # descriptor for the property to define a machine learning model to predict
    output_desc = RealDescriptor(
        key="density",
        units="g/cm^3",
        lower_bound=0.0,
        upper_bound=100.0
    )


    # featurize the molecular structure
    featurizer = MolecularStructureFeaturizer(
        name='Molecular Featurizer',
        description="Featurize the Solvent's molecular structure using the default features.",
        descriptor=input_desc,
        features=['standard'],
    )

    # get the feature names
    features = project.descriptors.from_predictor_responses(
        predictor=featurizer,
        inputs=[input_desc]
    )
 
    # create AutoMLPredictor, using the feature names as inputs
    # note: the molecular structure, `input_desc`, should not be included in the inputs here
    ml_predictor = AutoMLPredictor(
        name='ML Model for Density',
        description='Predict the density, given molecular features of the solvent',
        inputs = features,
        output = output_desc,
        training_data = []
    )
 
    # use a graph predictor to wrap together the featurizer and the machine learning model
    graph_predictor = GraphPredictor(
        name='Density from solvent molecular structure',
        description='Predict the density from the solvent molecular structure using molecular structure features.',
        predictors = [featurizer, ml_predictor],
        training_data = [GemTableDataSource(training_data_table_uid, 1)] # training data shared by all sub-predictors
    )
 
    # register or update predictor by name
    predictor = create_or_update(
        collection=project.predictors,
        module=graph_predictor
    )

Chemical Formula Featurizer
------------------------------------
The :class:`~citrine.informatics.predictors.chemical_formula_featurizer.ChemicalFormulaFeaturizer`
computes a configurable set of features on chemical formula data by using the properties of the individual elements
and their stoichiometric amounts.
Many of the features are stoichiometrically weighted generalized means of element-level properties, though some are more complex functions of the chemical formula.
The generalized means are configured with the ``powers`` argument, which is a list of means to calculate.
For example, setting ``powers=[1, 3]`` will calculate the mean and 3-mean of all applicable features.

The feature to compute are configured using the ``features`` and ``excludes`` arguments, which accept either feature names or predefined aliases.
The default is the `standard` alias, corresponding to a variety of features that are intuitive and often correlate with properties of interest.
Other aliases are "physical," "electronic," and "periodicTable."
A complete list of features and which aliases they map to can be found in the class docstring.

The feature names and descriptors are automatically constructed from the name of the input and the feature names.
The ``from_predictor_responses`` method will grab the descriptors for the features so that they can be fed into other predicors,
e.g., the :class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor`, as inputs.


The following example demonstrates how to use a :class:`~citrine.informatics.predictors.chemical_formula_featurizer.ChemicalFormulaFeaturizer` and
:class:`~citrine.informatics.predictors.auto_ml_predictor.AutoMLPredictor` to model a property of an alloy:

.. code:: python

    from citrine.informatics.descriptors import ChemicalFormulaDescriptor, RealDescriptor
    from citrine.informatics.predictors import ChemicalFormulaFeaturizer, AutoMLPredictor, GraphPredictor
    from citrine.seeding.find_or_create import create_or_update
    from citrine.informatics.data_sources import GemTableDataSource


    # descriptor for the chemical formula input
    input_desc = ChemicalFormulaDescriptor('Alloy chemical formula')
    # descriptor for the property to define a machine learning model to predict
    output_desc = RealDescriptor(
        key="melting temperature",
        units="Kelvin",
        lower_bound=300.0,
        upper_bound=5000.0
    )


    # featurize the chemical formula
    featurizer = ChemicalFormulaFeaturizer(
        name='ChemicalFeaturizer',
        description="Featurize the Alloy's chemical formula using the default features and a 2-mean.",
        descriptor=input_desc,
        features=['standard'],
        powers=[2]
    )

    # get the feature names
    features = project.descriptors.from_predictor_responses(
        predictor=featurizer,
        inputs=[input_desc]
    )

    # create AutoMLPredictor, using the feature names as inputs
    # note: the chemical formula, `input_desc`, should not be included in the inputs here
    ml_predictor = AutoMLPredictor(
        name='ML Model for Melting Temperature',
        description='Predict the melting temperature, given chemical features of the alloy',
        inputs = features,
        output = output_desc,
        training_data = []
    )

    # use a graph predictor to wrap together the featurizer and the machine learning model
    graph_predictor = GraphPredictor(
        name='Melting temperature from alloy chemical formula',
        description='Predict the melting temperature from the alloy chemical formula using chemical formula features.',
        predictors = [featurizer, ml_predictor],
        training_data = [GemTableDataSource(training_data_table_uid, 1)] # training data shared by all sub-predictors
    )

    # register or update predictor by name
    predictor = create_or_update(
        collection=project.predictors,
        module=graph_predictor
    )


Ingredients to formulation predictor (ALPHA)
--------------------------------------------------

The :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor` constructs a formulation from a list of ingredients.
This predictor is only required to construct formulations from CSV data sources.
Formulations are constructed automatically by GEM Tables when a ``formulation_descriptor`` is specified by the data source, so
an :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor` in not required in those cases.

Ingredients are specified by a map from ingredient id to the descriptor that contains the ingredient's quantity.
For example, ``{'water': RealDescriptor('water quantity', lower_bound=0, upper_bound=1, units='')}`` defines an ingredient ``water`` with quantity held by the descriptor ``water quantity``.
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
For example, we may wish to label ``water`` as a solvent and ``salt`` as a solute.
These labels are specified via:

.. code:: python

    labels = {"solvent": {"water'}, "solute": {"salt"}}

The following example illustrates how an :class:`~citrine.informatics.predictors.ingredients_to_formulation_predictor.IngredientsToFormulationPredictor` is constructed for the saline example.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    from citrine.informatics.predictors import IngredientsToFormulationPredictor

    file_link = dataset.files.upload("./saline_solutions.csv", "saline_solutions.csv")

    # create descriptors for each ingredient quantity (volume fraction)
    water_quantity = RealDescriptor(key='water quantity', 0, 1, units='')
    salt_quantity = RealDescriptor(key='salt quantity', 0, 1, units='')

    # create a descriptor to hold density data
    density = RealDescriptor(key='density', lower_bound=0, upper_bound=1000, units='g/cc')

    data_source = CSVDataSource(
        file_link = file_link,
        column_definitions = {
            'water quantity': water_quantity,
            'salt quantity': salt_quantity,
            'density': density
        },
        identifiers=['Ingredient id']
    )

    # create a descriptor to hold formulations
    formulation = FormulationDescriptor(key='formulation')

    IngredientsToFormulationPredictor(
        name='Ingredients to formulation predictor',
        description='Constructs a mixture from ingredient quantities',
        output=formulation,
        # map from ingredient id to its quantity
        id_to_quantity={
            'water': water_quantity,
            'salt': salt_quantity
        },
        # label water as a solvent and salt a solute
        labels={
            "solvent": {"water"},
            "solute": {"salt"}
        },
        training_data=[data_source]
    )


Simple mixture predictor
------------------------

Formulations may contain ingredients that are blends of other ingredients.
Along the lines of the example above, hypertonic saline can be mixed with water to form isotonic saline.
Often, the properties of a hierarchical mixture are strongly associated with its leaf ingredients.
The :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor` flattens a hierarchical recipe into a recipe that contains only those leaf ingredients.

The formulation to be flattened is specified by an ``input_descriptor`` formulation descriptor; the associated material history of the input formulation is traversed to determine the leaf ingredients.
These leaf ingredients are then summed across all leaves of the mixing processes, with the resulting candidates described by an ``output_descriptor`` formulation descriptor.
The ``training_data`` parameter is used as a source of formulation recipes to be used in flattening hierarchical mixtures.

The following example illustrates how a :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor` can be used to flatten the ingredients used in aqueous dilutions of hypertonic saline, yielding just the quantities of the leaf constituents salt and water.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor
    from citrine.informatics.predictors import SimpleMixturePredictor

    input_formulation = FormulationDescriptor(key='diluted saline')
    output_formulation = FormulationDescriptor(key='diluted saline (flattened)')

    # table with simple mixtures and their ingredients
    data_source = GemTableDataSource(table_id=table_uid, table_version=1, formulation_descriptor=input_descriptor)

    SimpleMixturePredictor(
        name='Simple mixture predictor',
        description='Constructs a formulation descriptor that flattens a hierarchy of simple mixtures into the quantities of leaf ingredients',
        input_descriptor=input_formulation,
        output_descriptor=output_formulation,
        training_data=[data_source]
    )

Mean property predictor
-----------------------

Often, properties of a mixture are proportional to the properties of its ingredients.
For example, the density of a saline solution can be computed from the densities of water and salt multiplied by their respective amounts:

.. math::

    d_{saline} = d_{water} * f_{water} + d_{salt} * f_{salt}

where :math:`d` is density and :math:`f` is relative ingredient fraction.
If the densities of water and salt are known, we can compute the expected density of a candidate mixture using this predictor.

The :class:`~citrine.informatics.predictors.mean_property_predictor.MeanPropertyPredictor` computes mean properties of formulation ingredients.
To configure a mean property predictor, we must specify:

* An input descriptor that holds the mixture's recipe and ingredient labels
* A list of properties to featurize
* The power of the `generalized mean <https://en.wikipedia.org/wiki/Generalized_mean>`_.
  Only integer powers are supported. ``p=1`` corresponds to the arithmetic mean, which weights
  all values evenly. Higher powers, such as ``p=2`` (the root mean square) place more weight
  on larger values of the property. Negative powers place more weight on smaller values.
* A data source that contains all ingredients and their properties
* How to handle missing ingredient properties

An optional label may also be specified if the mean should only be computed over ingredients given a specific label.

Missing ingredient properties can be handled one of three ways:

1. If ``impute_properties == False``, all ingredients must define a value for all featurized properties.
   Otherwise, the row will not be featurized.
   Use this option if you expect ingredient properties to be dense (always present) and would like to exclude rows when properties are missing.
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

If ``impute_properties == False``, any mixture that includes boric acid will not be featurized.
If ``impute_properties == True`` and no ``default_properties`` are specified, an density of :math:`\left( 1.0 + 2.16 \right) / 2 = 1.58` will be used.
If a value other than 1.58 should be used, e.g. 2.0, this can be specified by setting ``default_properties = {'density': 2.0}``.

The example below show how to configure a mean property predictor to compute mean solute density in formulations.

.. code:: python

    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.descriptors import FormulationDescriptor, RealDescriptor
    from citrine.informatics.predictors import MeanPropertyPredictor

    # descriptor that holds formulation data
    formulation = FormulationDescriptor(key='formulation')

    # property descriptor to featurize
    density = RealDescriptor(key='density', lower_bound=0, upper_bound=100, units='g/cm^3')

    # table with formulations and their ingredients
    data_source = GemTableDataSource(table_id=table_uid, table_version=1, formulation_descriptor=formulation)

    mean_property_predictor = MeanPropertyPredictor(
        name='Mean property predictor',
        description='Computes 1-mean ingredient properties',
        input_descriptor=formulation,
        # featurize ingredient density
        properties=[density],
        # compute the arithmetic mean
        p=1,
        training_data=[data_source],
        # impute ingredient properties, if missing
        impute_properties=True,
        # if missing, use with 2.0
        default_properties={'density': 2.0},
        # only featurize ingredients labeled as a solute
        label='solute'
    )

This predictor will compute a real descriptor with a key ``mean of property density with label solute in formulation`` which can be retrieved using:

.. code:: python

    mean_property_descriptors = project.descriptors.from_predictor_responses(
        predictor=mean_property_predictor, 
        inputs=[formulation_descriptor]
    )

If ``p`` is given a value other than ``1``, that value will be included in the key for the feature, e.g. ``2.0-mean of property viscosity``.

Ingredient fractions predictor
------------------------------

The :class:`~citrine.informatics.predictors.ingredient_fractions_predictor.IngredientFractionsPredictor` featurizes ingredient fractions in a formulation.
The predictor is configured by specifying a descriptor that contains formulation data and a list of known ingredients to featurize.
The list of ingredients should be the list of all possible ingredients for the input mixture.
If the mixture contains an ingredient that wasn't specified when the predictor was created, an error will be thrown.

For each featurized ingredient, the predictor will inspect the recipe and compute a response equal to the ingredient's total fraction in the recipe.
If an ingredient is not present in the mixture's recipe, the response for that ingredient fraction will be 0.
For example, given a formulation descriptor with key "formulation", a recipe ``{'water': 0.9, 'salt': 0.1}``, and ingredients ``['water', 'salt', 'boric acid']``,
this predictor would compute outputs:

- ``water share in formulation == 0.9``
- ``salt share in formulation == 0.1``
- ``boric acid share in formulation == 0.0``

The example below shows how to configure an ``IngredientFractionsPredictor`` that computes these responses.

.. code:: python

    from citrine.informatics.predictors import IngredientFractionsPredictor
    from citrine.informatics.descriptors import FormulationDescriptor

    formulation_descriptor = FormulationDescriptor(key='formulation')

    ingredient_fractions = IngredientFractionsPredictor(
        name='Ingredient Fractions Predictor',
        description='Computes fractions of provided ingredients',
        input_descriptor=formulation_descriptor,
        ingredients=['water', 'salt', 'boric acid']
    )

The response descriptors can be retrieved using:

.. code:: python

    ingredient_fraction_descriptors = project.descriptors.from_predictor_responses(
        predictor=ingredient_fractions,
        inputs=[formulation_descriptor]
    )

This will return a real descriptor for each featurized ingredient with bounds ``[0, 1]`` and key in the form ``'{ingredient} share in {formulation key}'``
where ```{formulation key}``` is "formulation" and ``{ingredient}`` is either ``water``, ``salt`` or ``boric acid``.

Label fractions predictor
-------------------------

The :class:`~citrine.informatics.predictors.label_fractions_predictor.LabelFractionsPredictor` computes total fraction of ingredients with a given label.
The predictor is configured by specifying a formulation descriptor that holds formulation data (i.e. recipes and ingredient labels) and a set of labels to featurize.
A separate response is computed for each featurized label by summing all quantities in the recipe associated with ingredients given the label.

The following example demonstrates how to create a predictor that computes the total fractions of solute and solvent in a formulation.

.. code:: python

    from citrine.informatics.descriptors import FormulationDescriptor
    # descriptor that holds formulation data
    formulation_descriptor = FormulationDescriptor(key='formulation')

    label_fractions = LabelFractionsPredictor(
        name='Saline solution label fractions',
        description='Computes total fraction of solute and solvent',
        input_descriptor=formulation_descriptor,
        labels={'solute', 'solvent'}
    )

This predictor will compute 2 responses, ``solute share in formulation`` and ``solvent share in formulation``, which can be retrieved using:

.. code:: python

    label_fractions_descriptors = project.descriptors.from_predictor_responses(
        predictor=label_fractions,
        inputs=[formulation_descriptor]
    )


Simple ML predictor
-------------------

The :class:`~citrine.informatics.predictors.simple_ml_predictor.SimpleMLPredictor` predicts material properties using a machine-learned model.
Each predictor is defined by a set of inputs, outputs and latent variables.
Inputs are used as input features to the machine learning model.
Outputs are the properties that you would like the model to predict.
There must be at least one input and one output.
Latent variables are properties that you would like the model to predict and you think could also be useful in predicting the outputs.
If defined, latent variables are used to build hierarchical models.
One model is trained from inputs to latent variables, and another is trained from inputs and latent variables to outputs.
Thus, all inputs and latent variables are used to predict outputs.

Models are trained using data provided by a :class:`~citrine.informatics.data_sources.DataSource` specified when creating a predictor.

The following example demonstrates how to use the python SDK to create a :class:`~citrine.informatics.predictors.simple_ml_predictor.SimpleMLPredictor`, register the predictor to a project and wait for validation:

.. code:: python

   from citrine import Citrine
   from citrine.seeding.find_or_create import (find_or_create_project,
                                               create_or_update 
                                              )
   from citrine.jobs.waiting import wait_while_validating 
   from citrine.informatics.predictors import SimpleMLPredictor
   from citrine.informatics.data_sources import GemTableDataSource

   # create a session with citrine using your API key
   session = Citrine(api_key=API_KEY)

   # find project by name 'Example project' or create it if not found
   project = find_or_create_project(project_collection=session.projects,
                                    project_name='Example project'
                                   )

   # create SimpleMLPredictor (assumes descriptors for
   # inputs/outputs/latent variables have already been created)
   simple_ml_predictor = SimpleMLPredictor(
       name = 'Predictor name',
       description = 'Predictor description',
       inputs = [input_descriptor_1, input_descriptor_2],
       outputs = [output_descriptor_1, output_descriptor_2],
       latent_variables = [latent_variable_descriptor_1],
       training_data = [GemTableDataSource(training_data_table_uid, 1)]
   )

   # register predictor or update predictor of same name if it already
   # exists in the project.
   predictor = create_or_update(collection=project.predictors,
                                resource=simple_ml_predictor
                               )

   # wait while the predictor is validating and print status information
   # while waiting.
   predictor = wait_while_validating(collection=project.predictors,
                                     module=predictor,
                                     print_status_info=True
                                    )

Often, a :class:`~citrine.informatics.predictors.simple_ml_predictor.SimpleMLPredictor` will include outputs from other predictors as inputs to its model.
Instead of entering these manually, outputs from a predictor can be retrieved programmatically using ``outputs = project.descriptors.from_predictor_responses(predictor, inputs)``, where ``outputs`` is the list of descriptors returned by the ``predictor`` given a list of descriptors as ``inputs``.

The following demonstrates how to create an :class:`~citrine.informatics.predictors.ingredient_fractions_predictor.IngredientFractionsPredictor` and use its outputs as inputs to a :class:`~citrine.informatics.predictors.simple_ml_predictor.SimpleMLPredictor`.

.. code:: python

    from citrine import Citrine
    from citrine.seeding.find_or_create import find_or_create_project
    from citrine.informatics.predictors import SimpleMLPredictor
    from citrine.informatics.data_sources import GemTableDataSource
    from citrine.informatics.predictors import IngredientFractionsPredictor
    from citrine.informatics.descriptors import FormulationDescriptor

    # create a session with citrine using your API key
    session = Citrine(api_key=API_KEY)

    # find project by name 'Example project' or create it if not found
    project = find_or_create_project(project_collection=session.projects,
                                     project_name='Example project'
                                    )

    # create a descriptor to store formulations
    formulation_descriptor = FormulationDescriptor(key='formulation')

    # create a predictor that computes ingredient fractions
    ingredient_fractions = IngredientFractionsPredictor(
        name = 'Ingredient Fractions Predictor',
        description = 'Computes fractions of provided ingredients',
        input_descriptor = formulation_descriptor,
        ingredients = ['water', 'salt', 'boric acid']
    )

    # get the descriptors the ingredient fractions predictor returns given the formulation descriptor
    ingredient_fraction_descriptors = project.descriptors.from_predictor_responses(
        predictor=ingredient_fractions, 
        inputs=[formulation_descriptor]
    )
    # ^^ in this case, ingredient_fraction_descriptors will contain 3 real descriptors: one for each featurized ingredient

    simple_ml_predictor = SimpleMLPredictor(
        name = 'Predictor name',
        description = 'Predictor description',
        inputs = ingredient_fraction_descriptors,
        outputs = [output_descriptor],
        latent_variables = [],
        training_data = GemTableDataSource(training_data_table_uid, 1, formulation_descriptor)
    )


Predictor reports
-----------------

A :doc:`predictor report <predictor_reports>` describes a machine-learned model, for example its settings and what features are important to the model. 
It does not include predictor evaluation metrics.
To learn more about predictor evaluation metrics, please see :doc:`PredictorEvaluationWorkflow <predictor_evaluation_workflows>`.

Training data
-------------

Training data are defined by a list of :doc:`data sources <data_sources>`.
When multiple data sources are specified, data from all sources is combined into a flattened list and deduplicated prior to training a predictor.
Deduplication is performed if a uid or identifier is shared between two or more rows.
The content of a deduplicated row will contain the union of data across all rows that share the same uid or at least 1 identifier.
An error will be thrown if two deduplicated rows contain different data for the same descriptor because it's unclear which value should be used in the deduplcated row.

Deduplication is additive.
Given three rows with identifiers ``[a]``, ``[b]`` and ``[a, b]``, deduplication will result in a single row with three identifiers (``[a, b, c]``) and the union of all data from these rows.
Care must be taken to ensure uids and identifiers aren't shared across multiple data sources to avoid unwanted deduplication.

When using a :class:`~citrine.informatics.predictors.graph_predictor.GraphPredictor`, training data provided by the graph predictor and all subpredictors are combined into a single deduplicated list.
Each predictor is trained on the subset of the combined data that is valid for the model.
Note, data may come from sources defined by other subpredictors in the graph.
Because training data are shared by all predictors in the graph, a data source does not need to be redefined by all subpredictors that require it.
If all data sources required train a predictor are specified elsewhere in the graph, the ``training_data`` parameter may be omitted.
If the graph contains a predictor that requires formulations data, e.g. a :class:`~citrine.informatics.predictors.simple_mixture_predictor.SimpleMixturePredictor` or :class:`~citrine.informatics.predictors.mean_property_predictor.MeanPropertyPredictor`, any GEM Tables specified by the graph predictor that contain formulation data must provide a formulation descriptor,
and this descriptor must match the input formulation descriptor of the sub-predictors that require these data.
