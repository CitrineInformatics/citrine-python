========================
Prohibited Data Patterns
========================

Summary
=======

This is a disclaimer on our end to let you know that there are some invalid usage patterns that are not prevented by the API but may corrupt your data and eliminate 
some of the functionality the api and/or platform would otherwise provide.

Cyclic data patterns
====================

Description
-----------

Data objects should **NOT** be linked in a cyclic pattern. Consider the following example (where the citrine session is created and dataset already defined):

>>> procsp = dataset.process_specs.register(ProcessSpec(name='test proc'))
>>> matsp = dataset.material_specs.register(MaterialSpec(name='test mat',process=procsp))
>>> ingsp = dataset.ingredient_specs.register(IngredientSpec(name='ing',material=matsp, process=procsp))
>>>

In this example, the following steps occurred:

1. A process was created.
2. A material was assigned the above process, which makes it an output material to that process.
3. An ingredient was assigned the above material and process, which makes it an input to that process belonging to that material.

This is a cyclic pattern because the material is an output to the process, but the ingredient (from the same material) is an input to the same process. 
In general, an object should not reference any other object in it's history to make a cyclic pattern.

Implications
------------

Currently, there are no validations in place to keep cyclic data from being persisted on the platform. It is up to the user to make sure that the 
objects created do not follow a cyclic pattern; otherwise, the data will be corrupted. If cyclic data is written to the platform, an error will 
not be thrown, but the user may lose core functionality (such as :code:`get_material_history()`) for the objects participating in the cycle.
