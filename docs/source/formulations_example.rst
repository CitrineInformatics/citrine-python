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
We have also measured the sugar fraction for some of the ingredients.

.. Note: An ingredient can have different labels when used in different mixtures.
    But to keep this example simple, we assume that an ingredient is always given all of the labels in the table below.


.. list-table:: Ingredients Data
   :widths: 25 25 25 25
   :header-rows: 1

   * - Name
     - Label(s)
     - Sucrose Fraction
     - Cost ($/kg)
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
The table below shows three example

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
   * - Margarita C
     -

Ingesting Data
--------------

Building a Table
----------------

Training and Analyzing a Model
------------------------------

Defining a Design Space
-----------------------

Proposing New Formulation Candidates
------------------------------------
