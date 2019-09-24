==========
Data Model
==========

Overview
--------

The Citrine python client is built on our NextGen data model, (codename taurus).
Taurus is a format that links together materials, the processes that produced them, and the measurements that characterize them.
Complete documentation can be found in the `data model docs <https://citrineinformatics.github.io/taurus/>`_.
This page presents a broad overview.

The Basic Objects: Processes, Materials, Measurements
-----------------------------------------------------

* A process is an action that creates a material, possibly using some input ingredients.
* A material represents a sample, either physical or virtual.
* A measurement characterizes a sample, either physically or computationally.
* An ingredient is a material and its amount that is used as an input to a process.

The links between objects must be established in a specific direction.
An ingredient specifies both the material it is derived from and the process it is used in.
A process does not specify either its input ingredients or the material it produces.
A material specifies the process that creates it, but does not specify what measurements are done on it or how it is used as an ingredient.
Measurements specify the material that they are performed on.

.. hint::

    First create the process, *then* create the output material, then create any measurements done on that material.
    If the material is used as an ingredient in a subsequent process, first create the new process, then create the ingredient
    that describes the materials role in the process.

We make a first class distinction between intent (specs) and reality (runs).
The same spec can be used to create many runs.
For example, you might create a single material spec for 10 cm silicon wafers and hundreds of associated material runs, one representing each physical sample produced.

It is often expected that a run and its spec will agree with each other but that is not enforced.
A measurement spec on the silicon wafers might state that the property "mass" is expected to have a value of 36.6 +/- 0.1 grams, but the measurement run on one sample has a value of 37.5 grams.
That is OK and *should* be recorded.
Materials science is messy and reality does not always align with our intent.
That's why we've made our data model flexible.

Attributes
----------

Properties are characteristics of a material that could be measured, e.g. chemical composition, density, yield strength.
Conditions are the environmental variables (typically measured) that may affect a process or measurement: e.g. Temperature, Pressure.
Parameters are the non-environmental variables (typically specified and controlled) that may affect a process or measurement: e.g. oven dial temperature position for a kiln firing, magnification for a measurement taken with a SEM.

Each type of object can be assigned some subset of these attributes.
For example, process specs have optional conditions and parameters but not properties.
For more information, please see the documentation related to each data object.

Templates and Validation
------------------------

Templates provide a controlled vocabulary that establishes what attributes you expect objects to have and what the bounds on those attributes are.
Attribute templates constrain a property, parameter, or condition to be within certain bounds.
Object templates contain a list of attribute templates that a process, material, or measurement may not violate.
If you attempt to upload an object with an attribute value that is outside of its associated bounds, you will receive a detailed error message.

.. note::

    Templates let you put guardrails on your objects, but they are not rigidly constraining.
    An object does *not* need to have an attribute for every one of the attribute templates in its object template.
    An object may have attributes with templates that do not exist in its object template; in fact, it may have attributes with no template at all.

Attribute templates should be narrowly scoped and very permissive.
For example, "Temperature is between 20 and 24 degC" is a bad template: temperature is generic and 20-24 degC is too strict.
"Room temperature during drying is between 0 and 100 degC" is better because it is more specific and contains all reasonable values of room temperature.
