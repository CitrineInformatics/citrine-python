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

These results can be further constrained by dataset:

.. code-block:: python

    dataset.process_templates.list()

The
:meth:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_tags`,
:meth:`~citrine.resources.data_objects.DataObjectCollection.filter_by_attribute_bounds`,
and :meth:`~citrine.resources.data_concepts.DataConceptsCollection.filter_by_name`
methods can help refine the listing to make the target object easier to find.

There also exist methods for locating data objects by its reference to another object:

Runs may be listed by spec with
:meth:`citrine.resources.material_run.MaterialRunCollection.list_by_spec`,
:meth:`citrine.resources.ingredient_run.IngredientRunCollection.list_by_spec`,
:meth:`citrine.resources.measurement_run.MeasurementRunCollection.list_by_spec`,
and :meth:`citrine.resources.process_run.ProcessRunCollection.list_by_spec`.

Material Runs may also be listed by their template with
:meth:`~citrine.resources.material_spec.MaterialSpecCollection.list_by_template`.

Specs may be listed by template with
:meth:`citrine.resources.material_spec.MaterialSpecCollection.list_by_template`,
:meth:`citrine.resources.process_spec.ProcessSpecCollection.list_by_template`,
and :meth:`citrine.resources.measurement_spec.MeasurementSpecCollection.list_by_template`.

The output material for a process can be located with
:meth:`citrine.resources.material_run.MaterialRunCollection.get_by_process`,
or :meth:`citrine.resources.material_run.MaterialRunCollection.get_by_process`.

The ingredients a material is used in can be located with
:meth:`citrine.resources.ingredient_run.IngredientRunCollection.list_by_material`,
or :meth:`citrine.resources.ingredient_spec.IngredientSpecCollection.list_by_material`.

The measurements of a material can be located with
:meth:`citrine.resources.measurement_run.MeasurementRunCollection.list_by_material`.

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
Sometimes, it is convenient to validate a group of runs and/or specs against their attribute and object
templates before any of the data objects are stored.
The ``.validate_templates()`` methods, available for all runs and specs, validate the provided object against all of the
(already-stored) attribute templates linked to attributes on the object as well as against an optional object template.
Notably, these methods do not validate linked objects in any way, making it possible to run validations on an object
with links to yet-unstored objects.
Be aware that this means that ``.validate_templates()`` will not surface any link-based errors.
This method returns a list of validation errors, which is empty on validation success.

The examples below illustrate the usage of ``.validate_templates()`` and its expected return values.

Example with validation errors with no object template:

.. code-block:: python

    condition1 = Condition('condition_name', value=UniformInteger(1, 2))
    condition2 = Condition('condition_name', value=UniformInteger(1, 3))
    parameter1 = Parameter('parameter_name', value=UniformInteger(1, 4))
    parameter2 = Parameter('parameter_name', value=UniformInteger(1, 5))
    process_spec = ProcessSpec(name='spec name')
    process_run = ProcessRun(name='run name', spec=process_spec, conditions=[condition1, condition2], parameters=[parameter1, parameter2])
    dataset.process_runs.validate_templates(process_run)

has return value:

.. code-block:: python

    [{'failure_message': 'Multiple Condition with named condition_name', 'property': None, 'failure_id': 'attribute.duplicate', 'input': None, 'type': NotImplemented},
     {'failure_message': 'Multiple Parameter with named parameter_name', 'property': None, 'failure_id': 'attribute.duplicate', 'input': None, 'type': NotImplemented}]

Example with validation errors with an object template:

.. code-block:: python

    condition_template = ConditionTemplate("condition template", bounds=IntegerBounds(1, 5))
    condition_template = dataset.condition_templates.register(condition_template)

    condition = Condition("condition", value=UniformInteger(1, 3), template=condition_template)
    process_template = ProcessTemplate("pt", conditions=[[LinkByUID("id", condition_template.uids["id"]), IntegerBounds(2, 4)]])
    process_spec = ProcessSpec("ps", template=process_template)
    process_run = ProcessRun("pr", conditions=[condition], spec=process_spec)
    dataset.process_runs.validate_templates(process_run, object_template=process_template)

has return value:

.. code-block:: python

    [{'failure_message': 'UniformInteger(1,3) extends below 2 {2}', 'property': None, 'failure_id': 'attribute.bounds.value', 'input': None, 'type': NotImplemented}]

For ingredients, the associated object template is a process template that is provided as a separate parameter. Any
value provided to the ``object_template`` parameter for an ingredient will be ignored.

Example with validation errors for an ingredient:

.. code-block:: python

    process_template = ProcessTemplate("pt", allowed_names=["foo"], allowed_labels=["bar"])
    process_spec = ProcessSpec("ps", template=process_template)

    mat_process_spec = ProcessSpec("mps")
    material_spec = MaterialSpec("ms", process=mat_process_spec)

    ingredient_spec = IngredientSpec("is", process=process_spec, material=material_spec, labels=["ingredient"])
    dataset.ingredient_specs.validate_templates(ingredient_spec, ingredient_process_template=process_template)

has return value:

.. code-block:: python

    [{'failure_message': 'Ingredient label ingredient not in list of allowed labels Set(bar)', 'property': None, 'failure_id': 'ingredient.label.allowed', 'input': None, 'type': NotImplemented},
     {'failure_message': 'Ingredient name is not in list of allowed names Set(foo)', 'property': None, 'failure_id': 'ingredient.name.allowed', 'input': None, 'type': NotImplemented}]
