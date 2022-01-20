================================
Teams User Management Migration
================================

Summary
=======

This is an FAQ about migrating your code to the :class:`~citrine.resources.team.Team` version of the Citrine Platform.

What's new?
====================

Teams
------

The biggest fundamental change that affects Citrine Python when migrating to CP2 is the
introduction of the Teams concept for access control. After this update, all projects and assets are owned by Teams that include one or more users on the platform. This concept was introduced to make it easier for Citrine Platform users to securely share assets across projects where it makes sense for their business.

Projects
---------
Projects are now available as a Team asset. Once you have a Project in hand, methods related to asset sharing and user management will direct you to the corresponding Team methods, and other methods will continue to work as expected. 

User Management
---------------
Many user management actions that were previously available on Projects are now only available on Teams.


How does this change my code?
=============================

The main change is that you should get the Project from the encompasing Team rather than the Citrine client.

.. code-block:: python

	# previously
	project = citrine.projects.get(project_id)
	# or
	project = citrine.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=citrine.projects,
		project_name="My Project"
	)


	# with Teams, you will use the Team collection instead
	team = citrine.teams.get(team_id)
	# or
	team = find_or_create_team(
		team_collection=citrine.teams,
		team_name="My Team"
	)

	# with which you can then find your project
	project = team.projects.get("baaa467e-1758-43a8-97c7-76e569d0dcab")
	# or
	project = team.projects.register(name="My Project")
	# or
	project = find_or_create_project(
		project_collection=team.projects,
		project_name="My Project"
	)


If your scripts managed user membership in projects, that user management now works on the team level instead.

.. code-block:: python

	# previously, for a given project
	project.add_user(user_uid)
	project.remove_user(user_uid)
	project.update_user_role(user_uid=user_uid, role=LEAD, actions=[WRITE])
	project.list_members()

	# after the migration to teams
	team.add_user(user_uid)
	team.remove_user(user_uid)
	team.update_user_action(user_uid=user_uid, actions=[WRITE])
	team.list_members()

