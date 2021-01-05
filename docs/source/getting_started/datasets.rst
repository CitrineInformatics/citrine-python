========
Datasets
========

A dataset is a collection of data objects and files.
It is a basic unit of access control, similar to projects: a user with read/write access on a dataset can read/write **all** of the resources in that dataset.
A dataset is owned by a specific project, but it may be shared with other projects as well.
Objects in a dataset may reference objects in a *different* dataset, hence a single user might not be able to view all of the relevant information about a material.

How to best organize your data into datasets is up to you, but please keep the following in mind:

* Everything contained within a dataset has the same level of access control.
  If you want to share different objects with different projects, then they should be in different datasets.
* The more datasets you have, the harder some tasks will be.
  This includes humain maintenance tasks like auditing access control settings, describing the contents of the dataset, and keeping metadata up to date.
  It also includes requests of the platform: some API calls will be slower if there are more datasets.

Datasets can be listed and gotten from projects just as projects are from the client itself:

.. code-block:: python

    project = citrine.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
    datasets_in_project = project.datasets.list()
    a_dataset = project.datasets.get("6ed8bf3b-876b-40f0-9d50-982e686e5cd3")

Datasets can only be deleted if they are empty.

Dataset Access and Sharing
--------------------------

When a dataset is created on the Citrine platform, only members of the project in which it was created can see it and interact with it.
If a dataset is made public it can be retrieved by any user using any project.
Once retrieved, its data objects are also available to view.
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

Files
-----

In addition to data objects, a dataset can also contain files.
These could be images output by a microscope in a proprietary format, a picture of how several samples are arranged on a hot plate, or anything else you would like to save.
The association of a file with a resource is done using a :class:`FileLink <citrine.resources.file_link.FileLink>`, which is created when you upload a file.
The `FileLink` can be associated with runs, specs, attributes and templates, all of which have a `file_links` field, and it can be used to download the file.

Uniqueness and Versioning
^^^^^^^^^^^^^^^^^^^^^^^^^

All FileLink objects are associated with a specific dataset, and they are given a `filename`
when uploaded. The `filename` **must be unique** within the dataset. If you upload another file
with the same `filename` it will be considered a new version of the same file. The old version
is not deleted, but at the moment you can only download the latest version of a given FileLink.

Uploading and Downloading Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assume you have a dataset named `dataset` and a file at the location `/Users/me/status_20190913.csv`
on your computer. The code below uploads the file and gives it the filename `microscope_status_20190913.csv`.
It then downloads the file back to your computer at `/Users/me/Downloads/settings.csv`.

.. code-block:: python

    file_link = dataset.files.upload(
        "/Users/me/status_20190913.csv", "microscope_status_20190913.csv")
    dataset.files.download(file_link,
        "/Users/me/Downloads/settings.csv")

Deleting Files
^^^^^^^^^^^^^^

If you have WRITE permission on a dataset then you may delete any file in the dataset.
Use this ability carefully, as there are no checks as to whether or no the file is referenced by
existing data objects.
Deleting a file can therefore produce broken links.

.. code-block:: python

    dataset.files.delete(file_link)
