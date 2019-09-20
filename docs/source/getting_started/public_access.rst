=======================
Dataset Access Control
=======================

Overview
--------

When a dataset is created on the Citrine platform, only members of the project in which it was
created can see it and interact with it. If a dataset is made public it can be retrieved by any user
using any project. Once retrieved, its data objects are also available to view. Datasets that are
public may only be written to by the project from which they originated.

Toggling Public Access
----------------------

A dataset can be made public (or made private again) using the project from which it originates
using the `make_public` and `make_private` methods on the project.

Example
-------

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
