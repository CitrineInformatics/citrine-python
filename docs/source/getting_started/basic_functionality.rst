==================
Managing Resources
==================

The Citrine python client can create, read, update, and delete resources.
This document describes those mechanics in general terms, without assuming a knowledge of what the resources are.

In general, for every resource type there is a corresponding collection.
For example, a :class:`~citrine.resources.project.ProjectCollection` contains :class:`Projects <citrine.resources.project.Project>`.
Generally, the collection is used to perform create/read/update/delete actions on the resources.
This pattern is illustrated in the examples below.


Creating
--------

To create a local resource, initialize it as you would any other python object. For example,

.. code-block:: python

    from citrine.resources.process_spec import ProcessSpec
    buy_electrolyte_spec = ProcessSpec("Buy ammonium chloride")

creates a process spec with the display name "Buy ammonium chloride" and no other information.

To persist a resource in the database, you must upload it using the ``register`` command of the relevant collection.
Assume there is a dataset ``battery_dataset_1``.
This dataset has an attribute `.process_specs`, representing the collection of all process specs.
The process spec collection has a `register` command, which registers the process spec, like so:

.. code-block:: python

    battery_dataset_1.process_specs.register(buy_electrolyte_spec)

If you tried to register the process spec to the dataset's material run collection, using ``battery_dataset_1.material_runs.register(buy_electrolyte_spec)``, then an error would result (since the types don't match).

The ``register`` command returns a copy of the resource as it now exists in the database.
The database may decorate the object with additional information, such as a unique identifier string that you can use to retrieve it in the future.

.. _functionality_reading_label:

Reading
-------

There are several ways to retrieve a resource from the database.

Get
^^^

Get retrieves a specific resource with a known unique identifier string.
If the project ``ceramic_resistors_project`` has a dataset with an id that you have saved as ``special_dataset_id``, then you could retrieve it with:

.. code-block:: python

    ceramic_resistors_project.datasets.get(special_dataset_id)

List
^^^^

List returns an iterator of every resource in a collection.
To list every design space in the project ``uv_absorbing_glasses``, use the command:

.. code-block:: python

    uv_absorbing_glasses.design_spaces.list()

Updating
--------

The ``update`` command updates an object. The following code creates and persists
a process spec ``sintering`` to a dataset ``tungsten_dataset``, then updates it locally
and persists that update.

.. code-block:: python

    sintering = tungsten_dataset.register(ProcessSpec(name="Sinter a powder"))
    sintering.notes = "Forgot to add notes!"
    tungsten_dataset.update(sintering)


Deleting
--------

Resources can generally be deleted with the ``delete`` command.
However, resources may link to other resources, and deleting these interconnected objects is tricky.
For more information, see the section on :ref:`deleting data objects <deleting_data_objects_label>`.

AI modules cannot be deleted, but they can be :ref:`archived <archiving_label>`.

Data Model Object Specific Methods
-----------------------------------

The client supports additional methods on certain data model object resources, such as more powerful ways to get resources.
These are detailed in the documentation of :doc:`GEMD data objects <../data_entry>`
