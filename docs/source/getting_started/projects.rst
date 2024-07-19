========
Projects
========

A Project is the basic container for AI Assets on the Citrine Platform, such as GEM Tables, Predictors, Design Spaces, and Design Workflows.
Access rights on resources inside a Project are managed, granted, and revoked at the Team level.

Users are individuals using the Citrine Platform, and they are made members of Team.
A user who is a member of a Team has access to all of the Projects that the Team has access to.

Every interaction with every other type of resource is scoped to a single Team.
This means that the same user can have different permissions on a resource depending on which Team they are using to access it.
For example, imagine that a Dataset is owned by Team A and shared with Team B, but Team B only has read, not write, permissions.
Then a user who is a member of both Teams would be able to add new data if accessing it through Project A, but not if accessing it through Project B.

..
    We probably should talk about publishing, pulling, and sharing here at some point.

Basic Project Use
-----------------

Most commonly, the first thing you will want to do after connecting to the Citrine Platform is to find a certain Project.
Assume that you have created a :class:`~citrine.resources.team.Team` team object named ``team``.
To list all of the Projects in that team, use the ``list`` command.

.. code-block:: python

    team.projects.list()

To retrieve a Project in the team, either find the Project in the list:

.. code-block:: python

    project_name = "Copper oxides project"
    all_projects = team.projects.list()
    copper_oxides_project = next((project for project in all_projects
    if project.name == project_name), None)

or get it by unique identifier:

.. code-block:: python

    project = team.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
