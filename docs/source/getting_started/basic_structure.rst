======================================
Structure of the Citrine Python Client
======================================

There are three basic types of resources in the Citrine python client: projects, datasets, and data objects.
There is a corresponding collection for each type of resource, e.g. :class:`~citrine.resources.project.ProjectCollection` for :class:`~citrine.resources.project.Project`.

Projects
--------

A project is the basic unit of collaboration on the Citrine platform.
It contains all of the resources described below.
Every interaction with every other type of resource is scoped by a specific single project.
For example, in order to view a file, you must enter a specific project and can only view files visible to you and that project.

After connecting to the Citrine Platform with a :class:`~citrine.citrine.Citrine` client, you can list the projects on the platform with:

.. code-block:: python

    citrine.projects.list()

To enter a project that you are a member of, either find the project in the list:

.. code-block:: python

    project_name = "Copper oxides project"
    all_projects = citrine.projects.list()
    copper_oxides_project = next((project for project in all_projects
    if project.name == project_name), None)

or get it by unique identifier:

.. code-block:: python

    project = citrine.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

Datasets
--------

A dataset is a collection of :ref:`data-model-objects-label` and files.
It is the basic unit of granularity with regards to access: a user with read/write access on a dataset can read/write **all** of the resources in that dataset.
A dataset is owned by a specific project but may be shared with other projects as well.

How to best organize your data into datasets is up to you, but please keep the following in mind:

* Everything contained within a dataset has the same level of access control.
  If you want to share different objects with different projects, then they should be in different datasets.
* The more datasets you have, the harder some tasks will be.
  This includes humain maintence tasks like auditing access control settings, describing the contents of the dataset, and keeping metadata up to date.
  It also includes requests of the platform: some API calls will be slower if there are more datasets.

Datasets can be listed and gotten from projects just as projects are from the client itself:

.. code-block:: python

    project = citrine.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
    datasets_in_project = project.datasets.list()
    a_dataset = project.datasets.get("6ed8bf3b-876b-40f0-9d50-982e686e5cd3")


.. _data-model-objects-label:

Data Model Objects
------------------

Data model objects are realizations of the objects that make up our :doc:`data model <data_model>`.
Examples might include the template for a drying process or a specific powder diffraction measurement done on a specific aluminum sample.
Each data model object is contained within a dataset.
A data model object can link to other data model objects, some of which may be in *different* datasets that themselves could be in different projects.
For example, you could have a dataset that contains a set of zinc alloys and another dataset that contains a set of measurements on those alloys.
If those datasets are in different projects then it is possible that some users are able to view the measurements but not the materials, or vice-versa.

The :doc:`next section <basic_functionality>` describes more about registering and retrieving data model objects and other resources.
Each of the data model object types has its own collection.
For example, the :class:`~citrine.resources.material_spec.MaterialSpec` data model object type has a :class:`~citrine.resources.material_spec.MaterialSpecCollection` collection.
