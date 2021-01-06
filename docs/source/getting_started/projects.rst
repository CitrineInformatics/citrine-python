========
Projects
========

A Project is the basic unit of collaboration and access on the Citrine platform.
They are containers for other resources, such as Datasets and modules.
Access rights on resources inside a Project are managed, granted, and revoked at the Project level.

Users are individuals using the Citrine Platform, and they are given access to projects.
A user with access to a Project has access to all of the Datasets and AI Modules that the project has access to.

Every interaction with every other type of resource is scoped to a single Project.
This means that the same user can have different permissions on a resource depending on which Project they are using to access it.
For example, imagine that a Dataset is owned by Project A and shared with Project B, but Project B only has read, not write, permissions.
Then a user who has access to both Projects would be able to add new data if accessing it from Project A, but not if accessing it from Project B.

Basic Project Use
-----------------

Most commonly, the first thing you will want to do after connecting to the Citrine Platform is to find a certain project.
Assume that you have created a :class:`~citrine.citrine.Citrine` client object named ``citrine``.
To list all of the projects on the platform, use the `list` command.

.. code-block:: python

    citrine.projects.list()

To retrieve a project that you are a member of, either find the project in the list:

.. code-block:: python

    project_name = "Copper oxides project"
    all_projects = citrine.projects.list()
    copper_oxides_project = next((project for project in all_projects
    if project.name == project_name), None)

or get it by unique identifier:

.. code-block:: python

    project = citrine.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

Managing Users
--------------

There are two types of roles users can have, MEMBER and ADMIN.
There are two types of access permissions: READ and WRITE.
READ allows a user to view resources in a project.
WRITE allows them to modify those resources.
Users with the ADMIN role have both READ and WRITE access, and can also add or remove other users and change their roles and permissions.


There are several methods for managing Projects, Users, and user membership in Projects.


Listing Users in a Project
^^^^^^^^^^^^^^^^^^^^^^^^^^

Users in a Project can be listed using the :func:`~citrine.resources.project.Project.list_members` method.
The ``ProjectMember`` array returned from this method has the user's role in the project as well as a copy of the User and Project objects.

.. code-block:: python

     project = citrine.projects.register(name="Your Project")

     # List Members of a Project
     project_members = project.list_members()

     # See their roles
     [(m.user.screen_name, m.role) for m in project_members]


Add User to a Project
^^^^^^^^^^^^^^^^^^^^^

Users can be added to a Project. They will be granted READ access to resources in the Project and will be given the
role MEMBER. This is accomplished with the :func:`~citrine.resources.project.Project.add_user` method.

.. code-block:: python

    # Get the UUID of the user you'd like to add
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Add them to your project
    project.add_user(user_id)


Remove User from a Project
^^^^^^^^^^^^^^^^^^^^^^^^^^

Users can also be removed from a Project. This is achieved with the
:func:`~citrine.resources.project.Project.remove_user` method.

.. code-block:: python

    # Get the UUID fo the user you'd like to delete
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Remove them from the project
    project.remove_user(user_id)


Update User's Role and Actions in a Project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A user's role in a Project can be updated. The method
:func:`~citrine.resources.project.Project.update_user_role` facilitates changing a User's role.

.. code-block:: python

    import LEAD from project_roles
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Make the user a lead
    project.update_user_role(user_id, LEAD)


.. code-block:: python

    from project_roles import MEMBER, WRITE
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Make the user a member with write access
    project.update_user_role(user_id, MEMBER, [WRITE])
