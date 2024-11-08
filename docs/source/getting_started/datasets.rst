========
Datasets
========

A :class:`~citrine.resources.dataset.Dataset` is a collection of data objects and files.
It is a basic unit of access control: a user with read/write access on a Dataset can read/write **all** of the resources in that Dataset.
A Dataset is owned by a specific Team, but it may be shared with other Teams as well.
Objects in a Dataset may reference objects in a *different* Dataset; hence, a single user might not be able to view all of the relevant information about a material.

How to best organize your data into Datasets is up to you, but please keep the following in mind:

* Everything contained within a Dataset has the same level of access control.
  If you want to share different objects with different Teams, then they should be in different Datasets.
* The more Datasets you have, the harder some tasks will be.
  This includes human maintenance tasks like auditing access control settings, describing the contents of the dataset, and keeping metadata up to date.
  It also includes requests of the platform: some API calls will be slower if there are more datasets.

Datasets can be listed and gotten from Teams just as Teams are from the client itself:

.. code-block:: python

    team = citrine.teams.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
    datasets_in_team = team.datasets.list()
    a_dataset = project.datasets.get("6ed8bf3b-876b-40f0-9d50-982e686e5cd3")

Datasets can only be deleted if they are empty.
If you need to delete a non-empty Dataset, see this discussion on :ref:`deleting data objects <deleting_data_objects_label>`.

Dataset Creation and Deletion
-----------------------------
A Dataset can be created (or deleted) from its team using the register and delete methods. Note that the creation of a Dataset requires the creation of a ``Dataset`` object.

Creating a Dataset
^^^^^^^^^^^^^^^^^^

To create a Dataset, the ``Dataset`` object must first be instantiated, and then passed to the registration endpoint.

Example
^^^^^^^
Assume you have a "band gaps team" with known id, ``band_gaps_team_id``, and are trying to make a Dataset within that team.

.. code-block:: python

    from citrine.resources.dataset import Dataset

    # get the team the dataset will belong to
    band_gaps_team = citrine.teams.get(band_gaps_team_id)

    # create the Dataset object
    Strehlow_Cook_description = "Band gaps for elemental and binary semiconductors with phase and temperature of measurement. DOI 10.1063/1.3253115"
    Strehlow_Cook_dataset = Dataset(name="Strehlow and Cook", summary="Strehlow and Cook band gaps", description=Strehlow_Cook_description)

    # pass the Dataset object to the registration endpoint
    Strehlow_Cook_dataset = band_gaps_team.datasets.register(Strehlow_Cook_dataset)


Deleting a Dataset
^^^^^^^^^^^^^^^^^^

A Dataset can be deleted using the team from which it originates. Note that the Dataset must be empty before deleting it.

Example
^^^^^^^

Assume you have a "band gaps team" with known id, ``band_gaps_team_id``, and are trying to delete a Dataset within that project with known id, ``strehlow_cook_dataset_id``.

.. code-block:: python

    # get the team the dataset is in
    band_gaps_team = citrine.teams.get(band_gaps_team_id)

    # delete the dataset
    band_gaps_team.datasets.delete(strehlow_cook_dataset_id)
   

Dataset Access, Sharing, and Transfer
-------------------------------------

Immediately after a Dataset is created on the Citrine Platform, only members of the Team in which it was created can see it and interact with it.

Sharing With a Specific Team
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A Dataset can be shared with another team using the :func:`~citrine.resources.team.Team.share` method on the original project.

Example
^^^^^^^

Assume you have a "band gaps team" with known id, ``band_gaps_team_id``, and an associated Dataset with known id, ``strehlow_cook_dataset_id``.
You would like to share the "strehlow cook Dataset" with another team, "semiconductors team" with a known id ``semiconductors_id``.

Sharing a Dataset:

.. code-block:: python
    
    #get the team that owns the dataset
    band_gaps_team = citrine.team.get(band_gaps_team_id)

    #get the dataset you want to share
    strehlow_cook_dataset = band_gaps_team.datasets.get(strehlow_cook_dataset_id)
    
    #this shares the dataset with the id strehlow_cook_dataset_id with the team with the id semiconductors_id
    band_gaps_team.share(resource=strehlow_cook_dataset, target_team_id=semiconductors_id)

Files
-----

In addition to data objects, a Dataset can also contain files.
These could be images output by a microscope in a proprietary format, a sketch of how several samples are arranged on a hot plate, the report describing a set of experiments, or anything else you would like to save.
The association of a file with a resource is done using a :class:`~citrine.resources.file_link.FileLink`, which is created when you upload a file.
The ``FileLink`` can be associated with multiple runs, specs, attributes, and templates, all of which have a ``file_links`` field, and it can be used to download the file.

Uniqueness and Versioning
^^^^^^^^^^^^^^^^^^^^^^^^^

All ``FileLink`` objects are associated with a specific Dataset, and they are given a ``filename``
when uploaded. The ``filename`` **must be unique** within the Dataset. If you upload another file
with the same ``filename`` it will be considered a new version of the same file. The old version
is not deleted, but at the moment you can only download the latest version of a given ``FileLink``.

Uploading and Downloading Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assume you have a Dataset named ``dataset`` and a file at the location ``/Users/me/status_20190913.csv``
on your computer. The code below uploads the file and gives it the filename ``microscope_status_20190913.csv``.
It then downloads the file back to your computer at ``/Users/me/Downloads/settings.csv``.

.. code-block:: python

    file_link = dataset.files.upload(
        file_path="/Users/me/status_20190913.csv",
        dest_name="microscope_status_20190913.csv"
    )
    dataset.files.download(
        file_link=file_link,
        local_path="/Users/me/Downloads/settings.csv"
    )

Deleting Files
^^^^^^^^^^^^^^

If you have WRITE permission on a Dataset, then you may delete any file in the Dataset.
Use this ability carefully, as there are no checks as to whether or not the file is referenced by existing data objects.
Deleting a file can therefore produce broken links.

.. code-block:: python

    dataset.files.delete(file_link)
