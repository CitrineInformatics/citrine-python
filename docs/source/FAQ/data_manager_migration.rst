=============================
Migrating to Use Data Manager
=============================

Summary
=======

This guide provides users of Citrine Python background and instructions for migrating code to take
full advantage of Data Manager features and prepare for the future removal of endpoints that will
occur with Citrine Python v4.0.

The key change will be that Datasets are now assets of Teams, rather than Projects. The bulk of
code changes will be migrating calls that access collections of data objects and Datasets from a
Project-based method to a Team or Dataset-based method.

If you require any additional assistance migrating your Citrine Python code, do not hesitate to
reach out to your Citrine customer support team.

What’s new?
===========

Once Data Manager has been enabled on your deployment of the Citrine Platform, the primary change
that will affect Citrine Python code is that Datasets, formerly contained within a Project, are
rather assets of a Team. In other words, Teams contain both Datasets and Projects.

Projects still contain assets such as GemTables, Predictors, DesignSpaces, etc., but Datasets and
their contents are now at the level of a Team. Data within a Dataset (in the form of GEMD Objects,
Attributes, and Templates, as well as files) are only leveraged within a Project by creating a
GemTable.

After Data Manager is activated, any new Datasets created, either via Citrine Python or the
Citrine Platform web UI, will be created at a Team level, and will not be accessible via the
typical  `project.<Collection> endpoints`*. New collections, at both the Team and Dataset level,
will be available in v3.4 of Citrine Python.

*Newly-registered Datasets can be accessible via Project-based methods if pulled into a project
with project.pull_in_resource(resource=dataset). However, this is not recommended as endpoints
listing data by projects and the “pull_in” endpoint for datasets will be removed in 4.0.

How does this change my code?
=============================

The change in behavior is most localized to two sets of operations on Datasets and their
constituent GEMD data objects: Sharing and Project-based Collections.

Sharing
-------

**Within a Team**

Previously, sharing a Dataset from one Project to another was a 2-step process: first publishing
the Dataset to a Team, then pulling the Dataset into the new project. Now that all Datasets are
assets of teams, sharing within a team is unnecessary. All of the publish, un-publish, and
pull_in_resource endpoints, when applied to Datasets, will return a deprecation warning version
3.4 and above, and be removed in version 4.0.

.. list-table:: Table 1. Result of publish/pull endpoints on Datasets based on Citrine Python version
   :widths: 50 25 25 25
   :header-rows: 1

    * - Endpoint
      - <=3.4
      - 3.4>=v<4.0
      - >=4.0
    * - project.[publish/un_publish](<br>     resource=dataset<br>)
      - No-op
      - ←, but with a Deprecation Warning
      - Will return an error
    * - project.project.pull_in_resource(<br>     resource=dataset<br>)
      - Will pull dataset into project
      - ←, but with a Deprecation Warning
      - Will return an error

**Between Teams**

Sharing a Dataset from one project to another where those projects are in different Teams was a
3-step process: publishing to the Team, sharing from one Team to another, then pulling into a
Project. With Data Manager, only the sharing action is needed.

Previous code for sharing My Dataset from Project A in Team A to eventually use in a Training Set
in Project B in Team B:

.. code-block:: python

    project_a.publish(resource=my_dataset)
    team_a.share(
        resource=my_datset,
        target_team_id=team_b.uid,
    )
    project_b.pull_in_resource(resource=my_dataset)

Is now:

.. code-block:: python

    team_a.share(
        resource=my_datset,
        target_team_id=team_b.uid,
    )

Project-based Collections
-------------------------

As Datasets are now assets of Teams, typical ways to list(), get(), or otherwise manipulate
Datasets or data objects within a Project will undergo a deprecation cycle. As of v3.4, these
endpoints will still work as usual with a deprecation warning, but will be removed in v4.0. It is
therefore recommended to migrate your code from all project-based listing endpoints as soon as
possible to adhere to supported patterns and avoid any costly errors.

.. list-table:: Table 2: Project-based endpoints for data object collections that will be deprecated
   :widths: 50 50
   :header-rows: 1

    * - Existing Code
      - Prefered Method (Available in version>=3.4)
    * - project.[datasets/gemd_objects].list()
      - team.[datasets/gemd_objects].list()
         -or-
        dataset.[gemd_objects].list()
    * - project.[datasets/gemd_objects].get()
      - team.[datasets/gemd_objects].get()
         -or-
        dataset.[gemd_objects].get()
    * - project.[datasets/gemd_objects]....
      - team.[datasets/gemd_objects]....
         -or-
        dataset.[gemd_objects]....

Note again that even though these endpoints will still be operational, registration of any new
Datasets will be at a Team level and thus inaccessible via these Project-based collections,
unless “pulled in” to a specific Project in that Team.