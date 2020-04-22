.. data_entry:

Data Entry
=========================

Creating Data Model Objects
---------------------------------

Each data object and template in the GEMD_ data model has a corresponding resource in the Citrine Python Client.
For example, the :class:`citrine.resources.process_spec.ProcessSpec` class implements the ProcessSpec_ object in GEMD_.
The Citrine Python Client implementations are consistent with the GEMD_ model specification.

The Citrine Python Client is built on top of and entirely interoperable with the gemd-python_ package.
Any method that accepts the Citrine Python Client's implementations of data model objects should also accept those from GEMD.

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
The data model object collections that are defined with the project scope (such as `project.process_specs`) are read-only and will throw an error if their register method is called.

If you have GEMD_ objects, e.g. :class:`gemd.entity.object.process_spec.ProcessSpec`, you can register it just like the objects defined in the Citrine Python Client.


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

For material runs and specs, there exist additional types of filtering:
:func:`~citrine.resources.material_run.MaterialRunCollection.filter_by_spec`,
:func:`~citrine.resources.material_run.MaterialRunCollection.filter_by_template`,
and :func:`~citrine.resources.material_spec.MaterialSpecCollection.filter_by_template`.


Referencing Data Model Objects
---------------------------------

Many data model objects contain links to other data model objects.
For example, a :class:`~citrine.resources.material_spec.MaterialSpec` references the :class:`~citrine.resources.process_spec.ProcessSpec` that produced it.
These links are created with the :class:`~gemd.entity.link_by_uid.LinkByUID` class, e.g.:

.. code-block:: python

    process = ProcessSpec("my process", uids={"my namespace": "my process"})
    dataset.process_specs.register(process)
    link = LinkByUID(scope="my namespace", id="my_process")
    material = MaterialSpec("my material", process=link)
    dataset.material_specs.register(material)

.. _GEMD: https://citrineinformatics.github.io/gemd-docs/
.. _ProcessSpec: https://citrineinformatics.github.io/gemd-docs/specification/objects/#process-spec
.. _gemd-python: https://github.com/CitrineInformatics/gemd-python
.. _UUID4: https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)

Validating Data Model Objects
---------------------------------

Dry-Run Validation
^^^^^^^^^^^^^^^^^^^^^^^^^

If you try to ``register`` or ``delete`` an invalid data model object, the operation fails with an error message that
specifies in what way(s) the data model object was invalid. For example:

.. code-block:: python

    spec = ProcessSpec("foo")
    run = ProcessRun("bar", spec=spec)

    spec = dataset.process_specs.register(spec)
    run = dataset.process_runs.register(run)

    dataset.process_specs.delete(spec.uids["id"])

yields

.. code-block::

    ERROR:citrine._session:400 DELETE projects/$PROJECT_ID/datasets/$DATASET_ID/process-specs/id/$PROCESS_SPEC_ID
    ERROR:citrine._session:{"code":400,"message":"object $PROCESS_SPEC_ID in dataset $DATASET_ID not deleted. See ValidationErrors for details.","validation_errors":[{"failure_message":"Referenced by process_run in dataset $DATASET_ID with ID $PROCESS_RUN_ID","failure_id":"object.mutation.referenced"}]}

If you want to run these same validations on a data model object without the possibility of registering or deleting the
object, pass the ``dry_run=True`` argument to either the ``register`` or ``delete`` method. In the example above, this
would look like

.. code-block:: python

    dataset.process_specs.delete(spec.uids["id"], dry_run=True)

Setting ``dry_run=True`` in either ``register`` or ``delete`` causes the method to run through all of its validations
and if any fail, provide the same error that the method would provide without the ``dry_run`` argument. If all
validations succeed, the method returns the same success value that it would without the ``dry_run`` argument, but the
object will not be registered or deleted.

Setting ``dry_run=False`` is equivalent to not specifying ``dry_run`` at all and will have no effect.

Template and Simple Validations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sometimes, it is convenient to be able to bulk validate a group of runs and/or specs against their attribute and object
templates before any of the data objects is stored. The ``.validate_templates()`` methods, available for all runs and
specs, validate the provided object against already-stored attribute templates as well as a provided object template.
Notably, these methods do not validate linked objects in any way, making it possible to run validations on an object
with links to yet-unstored objects. Be aware that this means that ``.validate_templates()`` does not validate links and
will not surface any link-based errors. For ingredients, the associated object template is a process template that is
provided as a separate parameter. This method returns a list of validation errors, which is empty on validation success.

The below example usages are trivial examples intended to illustrate the method arguments, rather than interesting
validation cases.

Example usage with no object template:

.. code-block:: python

    spec = ProcessSpec("foo")
    run = ProcessRun("bar", spec=spec)
    dataset.process_runs.validate_templates(run)

Example usage with an object template:

.. code-block:: python

    template = ProcessTemplate("pt")
    spec = ProcessSpec("foo", template=template)
    run = ProcessRun("bar", spec=spec)
    dataset.process_runs.validate_templates(run, object_template=template)

Example usage for an ingredient:

.. code-block:: python

    process_template = ProcessTemplate("pt")
    process_spec = ProcessSpec("ps", template=process_template)
    material_spec = MaterialSpec("ms", process=process_spec)
    ingredient_spec = IngredientSpec("is", process=process_spec, material=material_spec)
    dataset.ingredient_specs.validate_templates(run, ingredient_process_template=process_template)
