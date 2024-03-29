================================
Teams User Management Migration
================================

Summary
=======

This is an FAQ about migrating your code to the :class:`~citrine.resources.team.Team` version of
the Citrine Platform.

What's new?
====================

Teams
------

The biggest change is the introduction of teams for access control. After this update, all projects
and assets will be owned by teams that include one or more users on the platform. This concept was
introduced to make it easier for Citrine Platform users to securely share assets across projects.

Projects
---------
Projects are now available as ``Team`` assets. Project methods related to asset sharing and user
management will direct you to the corresponding ``Team`` methods. Other methods will continue to work
as before.

User Management
---------------
Many user management actions that were previously available on projects are now only available on
teams. Attempting to use them on a ``Project`` will raise an error directing you to the equivalent
``Team`` method.


How does this change my code?
=============================

The main change is retrieving a ``Project`` from the encompassing ``Team`` rather than the
``Citrine`` client.

Previously:

.. code-block:: python

	project = citrine.projects.get(project_id)
	# or
	projects = citrine.projects.list()
	# or
	project = citrine.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=citrine.projects,
		project_name="My Project"
	)

The ``Team`` equivalent:

.. code-block:: python

	# You will lookup your team
	team = citrine.teams.get(team_id)
	# or
	team = find_or_create_team(
		team_collection=citrine.teams,
		team_name="My Team"
	)

	# Then find your project within the team
	project = team.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
	# or 
	projects = team.projects.list()
	# or
	project = team.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=team.projects,
		project_name="My Project"
	)

You should modify your code to make use of these new access patterns, but for backward 
compatibility purposes, the following methods will continue to work after the teams 
migration:

.. code-block:: python

	project = citrine.projects.get(project_id)
	
	projects = citrine.projects.list()


If your scripts managed user membership in projects, that user management now works on the team
level instead.

Previously:

.. code-block:: python

	project.add_user(user_uid)
	project.remove_user(user_uid)
	project.update_user_role(user_uid=user_uid, role=LEAD, actions=[WRITE])
	project.list_members()

The ``Team`` equivalent:

.. code-block:: python

  # adding a user to a team
  team.add_user(user_uid)

  # removing a user from a team
  team.remove_user(user_uid)

  # overwriting a user's permissions on a team
  team.update_user_action(user_id=user_uid, actions=[WRITE, READ, SHARE])
	
  # listing user's and their permissions on a team
  team.list_members()

As shown above, with the introduction of teams, roles are replaced by specifying a user's actions
as any combination of ``READ``, ``WRITE``, and ``SHARE``.

User permissions should be modified using the ``Team`` object, but for backward compatibility 
purposes, listing project members via ``project.list_members()`` will simply list members of 
the project's parent team.


