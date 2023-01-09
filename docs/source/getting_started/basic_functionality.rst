==================
Managing Resources
==================

The Citrine Python client can create, read, update, and delete resources.
This document describes those mechanics in general terms, without assuming a knowledge of what the resources are.

In general, for every resource type there is a corresponding collection.
For example, a :class:`~citrine.resources.project.ProjectCollection` contains :class:`Projects <citrine.resources.project.Project>`.
Generally, the collection is used to perform create/read/update/delete actions on the resources.
This pattern is illustrated in the examples below.


Creating
--------

To create a local resource, initialize it as you would any other Python object. For example,

.. code-block:: python

    from gemd import ProcessSpec
    buy_electrolyte_spec = ProcessSpec("Buy ammonium chloride")

creates a process spec with the display name "Buy ammonium chloride" and no other information.

To persist a resource in the database, you must upload it using the ``register`` command of the relevant collection.
Assume there is a dataset ``battery_dataset_1``.
This dataset has an attribute ``.process_specs``, which produces a :class:`~citrine.resources.process_spec.ProcessSpecCollection`.
The collection has a ``register`` command, which registers the :class:`~citrine.resources.process_spec.ProcessSpec`, like so:

.. code-block:: python

    battery_dataset_1.process_specs.register(buy_electrolyte_spec)

If you tried to register the process spec to the dataset's material run collection, using ``battery_dataset_1.material_runs.register(buy_electrolyte_spec)``, then an error would result since the types don't match.

The ``register`` command returns a copy of the resource as it now exists in the database.
The database may decorate the object with additional information, such as a unique identifier string that you can use to retrieve it in the future.

.. _functionality_reading_label:

Controlling Flow
----------------

It is often useful to know when a resource has completed validating, especially when subsequent lines of code involve the validated resource. The ``wait_while_validating`` function will pause execution of the script until the resource has successfully validated.

.. code-block:: python
    
    sintering_model = sintering_project.predictors.register(sintering_model)
    wait_while_validating(collection=sintering_project.predictors, module=sintering_model)
    
Similarly, the ``wait_while_executing`` function will wait for a design or performance evaluation workflow to complete executing.

.. code-block:: python
    
    pew_workflow = sintering_project.predictor_evaluation_workflows.register(pew_workflow)
    pew_workflow = wait_while_validating(collection=sintering_project.predictor_evaluation_workflows, module=pew_workflow)
    pew_ex = pew_workflow.trigger(sintering_model)
    wait_while_executing(collection=sintering_project.predictor_evaluation_executions, execution=pew_ex, print_status_info=True)

Checking Status
---------------

After registering an asset, the ``status`` command can be used to obtain a static readout of the state of the asset on the platform (e.g., VALID, INVALID, VALIDATING, SUCCEEDED, FAILED, INPROGRESS). 

.. code-block:: python

    sintering_model = sintering_project.predictors.register(sintering_model)
    sintering_model.status
    
The ``status_info`` command returns additional details about an asset's status that can be very useful for debugging.

.. code-block:: python

    sintering_model.status_info

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

AI modules cannot be deleted at this time, but they can be :ref:`archived <archiving_label>`.

Data Model Object Specific Methods
-----------------------------------

The client supports additional methods on certain data model object resources, such as more powerful ways to get resources.
These are detailed in the documentation of :doc:`GEMD data objects <../data_entry>`
