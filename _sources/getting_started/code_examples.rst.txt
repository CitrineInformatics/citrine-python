=============
Code Examples
=============

Create a Session
----------------

All interaction with the Citrine API begins by creating a Citrine session.
This session establishes a link to the Citrine platform with your API key.
Your API key is unique and must be kept secret.
Best practice is to store is as an environment variable, here named ``CITRINE_API_KEY``.
Assuming that your Citrine deployment is ``https://matsci.citrine-platform.com`` and uses port 443, the code below would establish a Citrine session.

.. code-block:: python

    from citrine import Citrine
    API_KEY = os.environ.get('CITRINE_API_KEY')
    API_SCHEME = 'https'
    API_HOST = 'matsci.citrine-platform.com'
    API_PORT = '443'
    citrine = Citrine(API_KEY, API_SCHEME, API_HOST, API_PORT)


Create a Project and Dataset
----------------------------

One of your first actions might be to create a new project and a dataset, which you and your collaborators can populate.
The code below creates a project and one dataset associated with it.
It also inspects the newly registered project to get its unique id.
Note that all resources are given descriptive names and summaries.

.. code-block:: python

    from citrine.resources.project import Project
    from citrine.resources.dataset import Dataset
    band_gaps_project = Project(name="Band gaps", description="Actual and DFT computed band gaps")
    band_gaps_project = citrine.projects.register(band_gaps_project)
    print("My new project has name {} and id {}".format(band_gaps_project.name, band_gaps_project.uid))

    Strehlow_Cook_description = "Band gaps for elemental and binary semiconductors with phase and temperature of measurement. DOI 10.1063/1.3253115"
    Strehlow_Cook_dataset = Dataset(display_name="Strehlow and Cook", summary="Strehlow and Cook band gaps", description=Strehlow_Cook_description)
    Strehlow_Cook_dataset = band_gaps_project.datasets.register(Strehlow_Cook_dataset)

Find an existing Project and Dataset
------------------------------------

Often you will work with existing resources.
The code below retrieves a project with the name "Copper oxides project" and a datset with a known unique id that is stored as ``dataset_A_uid``.
For more information on retrieving resources, see :ref:`Reading Resources <functionality_reading_label>`.

.. code-block:: python

    project_name = "Copper oxides project"
    all_projects = citrine.projects.list()
    copper_oxides_project = next((project for project in all_projects if project.name == project_name), None)
    assert copper_oxides_project is not None
    dataset_A = copper_oxides_project.datasets.get(uid=dataset_A_uid)

Find a template
---------------

Templates provide a controlled vocabulary for organizing your data, and should be established before uploading other data.
Generally you will work with existing templates.
The example below searches for a process template with the tag "Oven_17" and asserts that one result is returned.

.. code-block:: python

    firing_templates = template_project.process_templates.filter_by_tags(tags=["Oven_17"])
    assert len(firing_templates) == 1
    firing_template_17 = firing_templates[0]

Create a linked process, material, and measurement
--------------------------------------------------

Imagine you purchase some toluene, measure its index of refraction, and then use it as an ingredient in a chemical reaction.
The code below converts those actions into data model objects: the process of purchasing, the material of toluene, the optical measurement, and the use of the toluene as an ingredient in a subsequent process.
Specs relate the intent and runs relate what actually happened, which may or may not be the same.
This assumes that you have already created or retrieved the following:
a process template ``purchase_template``, a material template ``toluene_template``, a measurement template ``refractive_index_template``,
a condition template ``temperature_template``, a parameter template ``wavelength_template``, and a property template ``refractive_index_template``.

.. code-block:: python

    from citrine.attributes.condition import Condition
    from citrine.attributes.parameter import Parameter
    from citrine.attributes.property import Property
    from citrine.resources.ingredient_run import IngredientRun
    from citrine.resources.ingredient_spec import IngredientSpec
    from citrine.resources.material_run import MaterialRun
    from citrine.resources.material_spec import MaterialSpec
    from citrine.resources.measurement_run import MeasurementRun
    from citrine.resources.measurement_spec import MeasurementSpec
    from citrine.resources.process_run import ProcessRun
    from citrine.resources.process_spec import ProcessSpec

    buy_toluene_spec = solvents.process_specs.register(ProcessSpec("Buy toluene", template=purchase_template))
    toluene_spec = solvents.material_specs.register(MaterialSpec("Toluene", process=buy_toluene_spec, template=toluene_template))
    refractive_index_spec = solvents.measurement_specs.register(MeasurementSpec("Index of refraction", template=refractive_index_template,
        conditions=[Condition("Room temperature", template=temperature_template, value=NominalReal(22, 'degC'))],
        parameters=[Parameter("Optical wavelength", template=wavelength_template, value=NominalReal(633, 'nm'))]))
    toluene_ingredient_spec = solvents.ingredient_specs.register(IngredientSpec("Toluene solvent", absolute_quantity=NominalReal(34, 'mL')))

    buy_toluene_run = solvents.process_runs.register(ProcessRun("Buy 1 liter of toluene", tags=["lot2019-140B"], spec=buy_toluene_spec))
    toluene = solvents.material_runs.register(MaterialRun("Toluene", process=buy_toluene_run, spec=toluene_spec))
    refractive_index_run = solvents.measurement_runs.register(MeasurementRun("Index of refraction",
        spec=refractive_index_spec, material=toluene,
        conditions=[Condition("Room temperature", template=temperature_template, value=NominalReal(24, 'degC'))],
        parameters=[Parameter("Optical wavelength", template=wavelength_template, value=NominalReal(633, 'nm'))],
        properties=[Property("Refractive index", template=refractive_index_template, value=NominalReal(1.49, 'dimensionless'))]))
    toluene_ingredient = solvents.ingredient_runs.register(IngredientRun("Toluene solvent", absolute_quantity=NominalReal(40, 'mL'), notes="I poured too much!"))

Getting a material history
--------------------------

Continuing the above example, the following code would retrieve the material history for toluene by using its Citrine ID.

.. code-block:: python

    scope = 'id'
    uid = toluene.uids[scope]
    toluene_history = solvents.material_runs.get_history(scope=scope, id=uid)

`toluene_history` is a MaterialRun that can be traced back to see its spec, the measurement performed on it,
that measurement's spec, the process that created it, and that process's spec.
The following statements are true:

.. code-block:: python

    toluene_history.measurements == [refractive_index_run]
    toluene_history.measurements[0].spec == refractive_index_spec
    toluene_history.process == buy_toluene_run
    toluene_history.process.spec == toluene_history.spec.process == buy_toluene

Note that the material history does *not* include a reference to the ingredients derived from
the material. Traversal "forward in time" is not possible.