.. formulations_example:

Formulations Example
====================

The Citrine Platform is a powerful tool to analyze formulations data.
A formulation is, generally speaking, a mixture of mixtures.
Individual ingredients are mixed together to form more complex ingredients, which may themselves be mixed with other ingredients and/or mixtures, and so on.
Generally, the top-level formulation has some properties that we with to optimize.
The ingredients themselves may also have known properties, which are useful for understanding the properties of the top-level formulation.
In addition, each mixing process may be characterized by attributes such as the temperature of a reaction vessel or the speed of a mixing element.

The GEMD data model provides a way to record all of the information relevant to a formulations problem,
and Citrine's AI Engine turns this information into trained models that can predict the properties of novel formulations.
This section demonstrates how to express a complete formulations example in Citrine-python, from data ingestion to new candidate generation.

Example Raw Data
----------------

To demonstrate the formulations machinery, we consider a toy problem -- margaritas!
We scour our pantry and gather some ingredients, laid out in the table below.
Several ingredients have labels, which helps the Citrine Platform understand the relationships between ingredients.
We have also measured the sugar fraction for some of the ingredients, and we know the price per kilogram of each ingredient.

.. note:: An ingredient can have different labels when used in different mixtures.
    But to keep this example simple, we assume that a given ingredient always has all of the labels below whenever it is used.


.. list-table:: Ingredients Data
   :widths: 25 25 25 25
   :header-rows: 1

   * - Name
     - Label(s)
     - Sucrose Fraction
     - Price ($/kg)
   * - Sugar
     - Sweetener
     - 1.00
     - 2.30
   * - Water
     -
     - 0.00
     - 0.05
   * - Lime Juice
     - Acid
     - 0.03
     - 14.00
   * - Triple Sec
     - Sweetener, Alcohol
     - 0.36
     - 18.99
   * - Tequila
     - Alcohol
     -
     - 29.00
   * - Ice
     -
     -
     - 2.75

We begin by creating two types of simple syrup--a mixture of sugar and water.
The quantities are in units of mass fraction.


.. list-table:: Simple Syrup Data
   :widths: 25 25 25
   :header-rows: 1

   * - Name
     - Water Quantity
     - Sugar Quantity
   * - Simple Syrup A
     - 0.50
     - 0.50
   * - Simple Syrup B
     - 0.45
     - 0.55

We now create margaritas by mixing together a subset of ingredients and blending for some time.
The basic ingredients are labeled as described in the "Ingredients Data" table, and the simple syrups are given a "simple syrup" label.
In addition to the ingredient mass fractions, we record the blending time, in seconds.
The margaritas are judged on an ultra-rigorous "tastiness" scale, which ranges from 0.0 to 10.0
The table below shows two examples.

.. list-table:: Margarita Data
   :widths: 35 25 40 35 35 35 35 25 25 25
   :header-rows: 1

   * - Name
     - Tastiness
     - Blend Time (s)
     - Simple Syrup A Quantity
     - Simple Syrup B Quantity
     - Sugar Quantity
     - Lime Juice Quantity
     - Triple Sec Quantity
     - Tequila Quantity
     - Ice Quantity
   * - Margarita A
     - 6.3
     - 8.0
     - 0.20
     - 0.0
     - 0.0
     - 0.15
     - 0.0
     - 0.25
     - 0.40
   * - Margarita B
     - 5.4
     - 12.0
     - 0.0
     - 0.15
     - 0.0
     - 0.10
     - 0.10
     - 0.30
     - 0.35

Ingesting Data
--------------

Ingesting data to GEMD is best done with additional tooling to automate the process, and will not be demonstrated in detail here.
But we will highlight several crucial data objects and their inter-connections.

The parameters of the blending process and the properties of the ingredients/formulations correspond to `attribute templates`.
The name, bounds, and units on these templates will later be matched to descriptors in the AI Engine.
Make sure to set the bounds wide enough to encompass all anticipated use cases of the template.

.. code-block:: python

    # Assume we have already created a dataset, named "dataset."
    # Though not demonstrated here, it is useful to give templates custom ids so that they can be easily retrieved.
    blend_time_template = dataset.parameter_templates.register(
        ParameterTemplate("blend time", bounds=RealBounds(0, 60.0, "s"))
    )
    price_template = dataset.property_templates.register(
        PropertyTemplate("price", bounds=RealBounds(0, 100, "1/kg"))
    )
    sucrose_fraction_template = dataset.property_templates.register(
        PropertyTemplate("sucrose fraction", bounds=RealBounds(0, 1, ""))
    )
    tastiness_template = dataset.property_templates.register(
        PropertyTemplate("tastiness", bounds=RealBounds(0, 10, ""))
    )

The attribute templates are attached to relevant object templates.
For example, the process template to represent blending should include ``blend_time_template`` as a ``parameter``.

Although it contains no attributes, we should particular pay attention to the templates that represent the mixing processes.
These will be used to convert GEMD data into formulations.
It is possible to use different process templates to distinguish between different types of mixing, but here we use the one template to represesnt both types of mixing that occur (mixing the simple syrup and mixing the margarita ingredients).
The template includes a comprehensive list of all allowed names and labels.

.. code-block:: python

    mix_template = dataset.process_templates.register(
        ProcessTemplate(
            "mix"
            allowed_names=["simple syrup", "sugar", "water", "lime juice", "triple sec", "tequila", "ice"],
            allowed_labels=["sweetener", "acid", "alcohol", "simple syrup"]
        )
    )

Notice that "simple syrup" is an allowed ingredient name, but we do not distinguish between "simple syrup A" and "simple syrup B."
This reflects the fact that we only ever use one simple syrup in a mixing process.
The resulting table will have one column indicating which simple syrup was used and a second column indicating how much was used.
Distinguishing in this way between the unique id of the material ("simple syrup A," "simple syrup B," etc.) and the generic name of the ingredient ("simple syrup") is especially useful when there are many materials to choose from.

To fill out the example, we illustrate some of the objects involved in specifying the spec for a particular margarita recipe.
This assumes that the material specs for the raw ingredients and the simple syrups have already been uploaded.

.. code-block:: python

    mix_margarita_spec = dataset.process_specs.register(
        ProcessSpec(f"mix margarita B", template=mix_template)
    )
    dataset.ingredient_specs.register(
        IngredientSpec(
            "simple syrup",
            material=simple_syrup_B_spec,
            process=mix_margarita_spec,
            labels=["simple syrup"]
            mass_fraction=NominalReal(nominal=0.15, units="")
        )
    )
    dataset.ingredient_specs.register(
        IngredientSpec(
            "triple sec",
            material=triple_sec_spec,
            process=mix_margarita_spec,
            labels=["alcohol", "sweetener"],
            mass_fraction=NominalReal(nominal=0.1, units="")
        )
    )
    # register remaining ingredient specs....
    # Then register the resulting material spec.
    margarita_spec = dataset.material_specs.register(
        MaterialSpec(f"margarita B", process=mix_margarita_spec, template=margarita_template)
    )

This material spec is then fed as the sole ingredient into a "blend margarita B" process spec, which produces a "blended margarita B" material spec.
A measurement spec is attached to the material spec to measure "tastiness."
Finally, run objects are created corresponding to each spec, to represent what actually happened.
Whew!
That's a lot, which is why we have created additional tooling, both in code and in the GUI, to automate this process.

A rendering of this example material history is shown below.

.. figure:: _static/GEMD_history_example.png
    :align: center

    Material History for Blended Margarita B

Repeating this process once for each margarita sample, we can build up a rich dataset for machine learning.

Building a Table
----------------

Training and Analyzing a Model
------------------------------

Defining a Design Space
-----------------------

Proposing New Formulation Candidates
------------------------------------
