=======================
Projects and Users
=======================

Overview
--------

Projects are containers for other resources, such as datasets and modules.
Access rights on resources inside a Project are managed, granted, and revoked at the Project level.
This means a user can have permission to perform an action in one project, but be rejected because 
they are trying to do it from the wrong project. For example, consider Dataset A owned by Project A. 
There is also Project B that has read access to Dataset A. A user has access to Project A and Project B 
but cannot update or destroy Dataset A from Project B.

Users are individuals using of the Citrine Platform.
Users cannot directly access resources, but must instead be added to Projects.
Through their membership in Projects, Users can access resources.

This library presents several methods for managing Projects, Users, and user membership in Projects.


Listing Users in a Project
----------------------

Users in a Project can be listed using the :func:`~citrine.resources.project.Project.list_members` method.
The ProjectMember array returned from this method has the user's role in the project as well as a copy of the User and Project objects.

Add User to a Project
--------------------

Users can be added to a Project. They will be granted READ access to resources in the Project and will be given the
role "MEMBER". This is accomplished with the :func:`~citrine.resources.project.Project.add_user` method.

Remove User from a Project
-----------------------

Users can also be removed from a Project. This is achieved with the
:func:`~citrine.resources.project.Project.remove_user` method.

Update User's Role and Actions in a Project
---------------------------
A user's role in a Project can be updated. The method
:func:`~citrine.resources.project.Project.update_user_role` facilitates changing a User's role.

Examples
-------
Adding a User to a Project

.. code-block:: python

    # Get the UUID of the user you'd like to add
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Add them to your project
    project.add_user(user_id)


Remove a User from a Project

.. code-block:: python

    # Get the UUID fo the user you'd like to delete
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Remove them from the project
    project.remove_user(user_id)

Listing Users in a Project

.. code-block:: python

     project = citrine.projects.register(name="Your Project")

     # List Members of a Project
     project_members = project.list_members()

     # See their roles
     [(m.user.screen_name, m.role) for m in project_members]

Changing the role of a User in a Project

.. code-block:: python

    import LEAD from project_roles
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Change User Role in Project
    project.update_user_role(user_id, LEAD)

Specifying that a user is permitted the WRITE action in a Project

.. code-block:: python

    from project_roles import MEMBER, WRITE
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    project = citrine.projects.register(name="Your Project")

    # Change User Role in Project
    project.update_user_role(user_id, MEMBER, [WRITE])
