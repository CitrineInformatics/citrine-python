========
Datasets
========

A dataset is a collection of data objects and files.
It is a basic unit of access control: a user with read/write access on a dataset can read/write **all** of the resources in that dataset.
A dataset is owned by a specific project, but it may be shared with other projects as well.
Objects in a dataset may reference objects in a *different* dataset; hence, a single user might not be able to view all of the relevant information about a material.

How to best organize your data into datasets is up to you, but please keep the following in mind:

* Everything contained within a dataset has the same level of access control.
  If you want to share different objects with different projects, then they should be in different datasets.
* The more datasets you have, the harder some tasks will be.
  This includes human maintenance tasks like auditing access control settings, describing the contents of the dataset, and keeping metadata up to date.
  It also includes requests of the platform: some API calls will be slower if there are more datasets.

Datasets can be listed and gotten from projects just as projects are from the client itself:

.. code-block:: python

    project = citrine.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
    datasets_in_project = project.datasets.list()
    a_dataset = project.datasets.get("6ed8bf3b-876b-40f0-9d50-982e686e5cd3")

Datasets can only be deleted if they are empty.
If you need to delete a non-empty dataset, see this discussion on :ref:`deleting data objects <deleting_data_objects_label>`.

Dataset Creation and Deletion
-----------------------------
A dataset can be created (or deleted) using the project from which it should or currently originates using the :func:`~citrine.resources.dataset.DatasetCollection.register` and :func:`~citrine.resources.project.ProjectCollection.delete` methods. Note that the creation of a dataset requires the creation of a `Dataset` object.

Creating a Dataset
^^^^^^^^^^^^^^^^^^

To create a dataset, the `Dataset` object must first be instantiated, and then passed to the registration endpoint.

Example
^^^^^^^
Assume you have a "band gaps project" with known ID, `band_gaps_project_id`, and are trying to make a dataset within that project.

.. code-block:: python

    from citrine.resources.dataset import Dataset

    # get the project the dataset will belong to
    band_gaps_project = citrine.projects.get(band_gaps_project_id)

    # create the Dataset object
    Strehlow_Cook_description = "Band gaps for elemental and binary semiconductors with phase and temperature of measurement. DOI 10.1063/1.3253115"
    Strehlow_Cook_dataset = Dataset(name="Strehlow and Cook", summary="Strehlow and Cook band gaps", description=Strehlow_Cook_description)

    # pass the Dataset object to the registration endpoint
    Strehlow_Cook_dataset = band_gaps_project.datasets.register(Strehlow_Cook_dataset)


Deleting a Dataset
^^^^^^^^^^^^^^^^^^

A dataset can be deleted using the project from which it originates. Note that the dataset must be empty before deleting it. 

Example
^^^^^^^

Assume you have a "band gaps project" with known ID, `band_gaps_project_id`, and are trying to delete a dataset within that project with known ID, `strehlow_cook_dataset_id`.

.. code-block:: python

    # get the project the dataset is in
    band_gaps_project = citrine.projects.get(band_gaps_project_id)

    # delete the dataset
    band_gaps_project.datasets.delete(strehlow_cook_dataset_id)
   

Dataset Access, Sharing and Transfer
------------------------------------

When a dataset is created on the Citrine platform, only members of the project in which it was created can see it and interact with it.
If a dataset is made public, it (and its entire contents) can be retrieved by any user using any project.
Datasets that are public may only be written to by the project from which they originated.

Toggling Public Access
^^^^^^^^^^^^^^^^^^^^^^

A dataset can be made public (or made private again) using the project from which it originates
using the :func:`~citrine.resources.project.Project.make_public` and :func:`~citrine.resources.project.Project.make_private` methods on the project.

Example
^^^^^^^

Assume you have a "band gaps project" with known ID, `band_gaps_project_id`, and an associated dataset with known ID, `strehlow_cook_dataset_id`.

Making a dataset public:

.. code-block:: python

    band_gaps_project = citrine.projects.get(band_gaps_project_id)
    strehlow_cook_dataset = band_gaps_project.datasets.get(strehlow_cook_dataset_id)

    # Make the Strehlow and Cook dataset publicly accessible so that it can be retrieved
    # from any project
    band_gaps_project.make_public(strehlow_cook_dataset)

Making a dataset private:

.. code-block:: python

    band_gaps_project = citrine.projects.get(band_gaps_project_id)
    strehlow_cook_dataset = band_gaps_project.datasets.get(strehlow_cook_dataset_id)

    # If the Strehlow and Cook dataset was previously publicly available, revoke that
    # access so that it can only be retrieved and from the band_gaps_project.
    band_gaps_project.make_private(strehlow_cook_dataset)

Sharing With a Specific Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A dataset can be shared with another project using the :func:`~citrine.resources.project.Project.share` method on the original project.

Example
^^^^^^^

Assume you have a "band gaps project" with known ID, `band_gaps_project_id`, and an associated dataset with known ID, `strehlow_cook_dataset_id`. You would like to share the "strehlow cook dataset" with another project, "semiconductors project" with a known ID `semiconductors_id`.

Sharing a dataset:

.. code-block:: python
    
    #get the project that owns the dataset
    band_gaps_project = citrine.projects.get(band_gaps_project_id)
    
    #this shares the dataset with the ID strehlow_cook_dataset_id with the project with the ID semiconductors_id
    band_gaps_project.share(project_id=semiconductors_id, resource_type="DATASET", resource_id=strehlow_cook_dataset_id)

Transfering a Dataset to Another Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A dataset can be transfered to another project using the project from which is originates using the :func:`~citrine.resources.project.Project.transfer_resource` method on the project.

Example
^^^^^^^

Assume you have a "band gaps project" with known ID, `band_gaps_project_id`, and an associated dataset with known ID, `strehlow_cook_dataset_id`. You would like to transfer ownership of the "strehlow cook dataset" to another project, "semiconductors project" with a known ID `semiconductors_id`.

Transfering a dataset:

.. code-block:: python
    
    # get the project that owns the dataset
    band_gaps_project = citrine.projects.get(band_gaps_project_id)

    # get the dataset you would like to tranfer
    strehlow_cook_dataset = band_gaps_project.datasets.get(strehlow_cook_dataset_id)
    
    # transfer ownership of the strehlow_cook_dataset to another project with a known ID semiconductors_id
    band_gaps_project.transfer_resource(resource = strehlow_cook_dataset, receiving_project_uid = semiconductors_id)

Files
-----

In addition to data objects, a dataset can also contain files.
These could be images output by a microscope in a proprietary format, a sketch of how several samples are arranged on a hot plate, the report describing a set of experiments, or anything else you would like to save.
The association of a file with a resource is done using a :class:`~citrine.resources.file_link.FileLink`, which is created when you upload a file.
The ``FileLink`` can be associated with multiple runs, specs, attributes and templates, all of which have a ``file_links`` field, and it can be used to download the file.

Uniqueness and Versioning
^^^^^^^^^^^^^^^^^^^^^^^^^

All ``FileLink`` objects are associated with a specific dataset, and they are given a ``filename``
when uploaded. The ``filename`` **must be unique** within the dataset. If you upload another file
with the same ``filename`` it will be considered a new version of the same file. The old version
is not deleted, but at the moment you can only download the latest version of a given ``FileLink``.

Uploading and Downloading Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assume you have a dataset named ``dataset`` and a file at the location ``/Users/me/status_20190913.csv``
on your computer. The code below uploads the file and gives it the filename ``microscope_status_20190913.csv``.
It then downloads the file back to your computer at ``/Users/me/Downloads/settings.csv``.

.. code-block:: python

    file_link = dataset.files.upload(
        "/Users/me/status_20190913.csv", "microscope_status_20190913.csv")
    dataset.files.download(file_link,
        "/Users/me/Downloads/settings.csv")

Deleting Files
^^^^^^^^^^^^^^

If you have WRITE permission on a dataset then you may delete any file in the dataset.
Use this ability carefully, as there are no checks as to whether or not the file is referenced by existing data objects.
Deleting a file can therefore produce broken links.

.. code-block:: python

    dataset.files.delete(file_link)
