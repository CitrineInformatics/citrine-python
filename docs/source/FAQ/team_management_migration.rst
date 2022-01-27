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

The biggest change is the introduction of Teams for access control. After this update, all projects
and assets will be owned by Teams that include one or more users on the platform. This concept was
introduced to make it easier for Citrine Platform users to securely share assets across projects.

Projects
---------
Projects are now available as a Team asset. Project methods related to asset sharing and user
management will direct you to the corresponding Team methods. Other methods will continue to work
as before.

User Management
---------------
Many user management actions that were previously available on Projects are now only available on
Teams. Attempting to use them on a Project will raise an error with a message directing you towards
the equivalent Team method.


How does this change my code?
=============================

The main change is retrieving a Project from the encompasing Team rather than the Citrine client.

Previously:

.. code-block:: python

	project = citrine.projects.get(project_id)
	# or
	project = citrine.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=citrine.projects,
		project_name="My Project"
	)

The Teams equivalent:

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
	project = team.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=team.projects,
		project_name="My Project"
	)

If your scripts managed user membership in projects, that user management now works on the team
level instead.

Previously:

.. code-block:: python

	project.add_user(user_uid)
	project.remove_user(user_uid)
	project.update_user_role(user_uid=user_uid, role=LEAD, actions=[WRITE])
	project.list_members()

The Teams equivalent:

.. code-block:: python

	team.add_user(user_uid)
	team.remove_user(user_uid)
	team.update_user_action(user_uid=user_uid, actions=[WRITE, READ, SHARE])
	team.list_members()

As shown above, with the introduction of Teams, roles are replaced by specifying a user's actions
as any combination of READ, WRITE, and SHARE.
