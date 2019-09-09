===============================
Using the Citrine Python Client
===============================

The Citrine python client creates, reads, updates, and deletes :doc:`resources <basic_structure>` using the Citrine product API.

Creating
--------

To create a resource, initialize it as you would any other python object. For example,

.. code-block:: python

    from citrine.resources.process_spec import ProcessSpec
    buy_electrolyte_spec = ProcessSpec("Buy ammonium chloride")

creates a process spec with the display name "Buy ammonium chloride" and no other information.

To persist a resource in the database, you must upload it using the ``register`` command.
The following command uploads this process spec to the dataset ``battery_dataset_1``:

.. code-block:: python

    battery_dataset_1.process_specs.register(buy_electrolyte_spec)

You must specify the dataset, because all process specs are :ref:`associated with a dataset <data-model-objects-label>`, and the collection type, in this case ``.process_specs``.
The command ``battery_dataset_1.material_runs.register(buy_electrolyte_spec)``, which attempts to register a process spec to the collection of material runs, will result in an error.

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
To list every material spec in the dataset ``standard_glasses_dataset``, use the command:

.. code-block:: python

    standard_glasses_dataset.material_specs.list()

You can instead broaden the scope of the search to an entire project.
The command ``lens_project.material_specs.list()`` will list every material spec in every dataset that ``lens_project`` has read access to.

Filter
^^^^^^

Filter lies somewhere between Get and List, returning only those objects that meet a given criterion.
There are currently two ways to filter, and they only work on data model objects: :func:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_tags` and :func:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_attribute_bounds`.
As with List, filter can be scoped to a dataset or to a project.

Updating
--------

TBD

Deleting
--------

TBD
