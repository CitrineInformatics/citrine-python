.. data_entry:

Data Entry
=========================

Creating Data Model Objects
---------------------------------

Each data object and template in the GEMD_ data model has a corresponding resource in the Citrine Python Client.
For example, the :class:`citrine.resources.process_spec.ProcessSpec` class implements the ProcessSpec_ object in GEMD_.
The Citrine Python Client implementations are consistent with the GEMD_ model specification.

The Citrine Python Client is built on top of and entirely interoperable with the taurus_ package.
Any method that accepts the Citrine Python Client's implementations of data model objects should also accept those from taurus.

Identifiying Data Model Objects
---------------------------------

After registering a data model object, you will probably want to be able to find that object again.
The easiest way to get an existing object is by one of its unique identifiers.
Every data model object on the Citrine Platform has a platform-issued identifier, often referred to as the "Citrine Identifier" or "CitrineId".
These identifiers are UUID4_, which are extremely robust but also not especially human readable.

`Alternative identifiers`__ are an easier way to recall data objects.
To create an alternative identifier, simply add key-value pairs to the ``uids`` dictionary in the data model object.
The key defines the ``scope`` and the value the ``id``.
As a pair, they must be unique across the entire platform.
You can think of each value of ``scope`` as defining a namespace, with ``id`` being the name within that namespace.

__ https://citrineinformatics.github.io/gemd-docs/specification/unique-identifiers/#alternative-ids

Registering Data Model Objects
---------------------------------

Data model objects are created on the Citrine Platform through the ``register`` method present in each data model object collection that comes from a dataset.
For example:

.. code-block:: python

    dataset.process_specs.register(ProcessSpec(...))

Note that registration must be performed within the scope of a dataset: the dataset into which the objects are being written.
The data model object collections that are defined with the project scope are read-only and will throw an error if their register method is called.

If you have taurus_ objects, e.g. :class:`taurus.entity.object.process_spec.ProcessSpec`, you can register it just like the objects defined in the Citrine Python Client.


Finding Data Model Objects
---------------------------------

If you know any a data model object's unique identifiers, then you can get that object by its unique identifier.
For example:

.. code-block:: python

    project.process_templates.get(scope="standard-templates", id="milling")

If you don't know any of the data model object's unique identifiers, then you can list the data model objects and find your object in that list:

.. code-block:: python

    project.process_templates.list()

The 
:func:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_tags`,
:func:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_attribute_bounds`,
and :func:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_name`
can help refine the listing to make the target object easier to find.

Referencing Data Model Objects
---------------------------------

Many data model objects contain links to other data model objects.
For example, a :class:`~citrine.resources.material_spec.MaterialSpec` references the :class:`~citrine.resources.process_spec.ProcessSpec` that produced it.
These links are created with the :class:`~taurus.entity.link_by_uid.LinkByUID` class, e.g.:

.. code-block:: python

    process = ProcessSpec("my process", uids={"my namespace": "my process"})
    dataset.process_specs.register(process)
    link = LinkByUID(scope="my namespace", id="my_process")
    material = MaterialSpec("my material", process=link)
    dataset.material_specs.register(material)

.. _GEMD: https://citrineinformatics.github.io/gemd-docs/
.. _ProcessSpec: https://citrineinformatics.github.io/gemd-docs/specification/objects/#process-spec
.. _taurus: https://github.com/CitrineInformatics/taurus
.. _UUID4: https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)
