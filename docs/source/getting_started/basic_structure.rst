======================================
Structure of the Citrine Python Client
======================================

There are three basic types of resources in the Citrine python client.

Projects
--------

A project is the basic unit of collaboration on the Citrine platform.
It can contain all of the resources described below.
If a user is a member of a project then they have access to **all** of the resources that are in that project or have been shared with that project.

Datasets
--------

A dataset is a collection of :ref:`data-model-objects-label`.
It is the basic unit of granulatiry with regards to access: a user with read/write access on a dataset can read/write **all** of the resources in that dataset.
A dataset is associated with a project; anybody who has read/write access on that project will also have read/write access on its datasets.


How to best organize your data into datasets is up to you, as it makes actions like the following possible:

* When searching for objects that meet some criterion, you can limit your search to a particular dataset.
* You can share a dataset with another project.

.. _data-model-objects-label:

Data Model Objects
------------------

Data model objects are realizations of the objects that make up our :doc:`data model <data_model>`.
Examples might include the template for a drying process or a specific powder diffraction measurement done on a specific aluminum sample.
Data model objects are associated with a dataset.
A data model object can link to other data model objects, some of which may be in *different* datasets that themselves could be in different projects.
For example, you could have a dataset that contains a set of zinc alloys and another dataset that contains a set of measurements on those alloys.
If those datasets are in different projects then it is possible that some users are able to view the measurements but not the materials, or vice-versa.
