========
Teams
========

Teams were introduced to simplify securely sharing your assets across projects. All assets
are owned by Teams, including projects.

.. warning::
    Teams are not available on all Citrine Platform deployments.

    Please contact support for more information.

Basic Team Use
-----------------

In the following examples, ``citrine`` is the name of your :class:`~citrine.citrine.Citrine`
client object.

After connecting to the Citrine Platform, you'll most likely want to find a specific Team.
To list all Teams of which you are a member, use the ``list`` method.

.. code-block:: python

    citrine.teams.list()

There are a few ways to find a single Team from this list.

.. code-block:: python

    # 1. Iterate over the list of teams and filter by name.
    team_name = "Team A"
    all_teams = citrine.teams.list()
    team_a = next((team for team in all_teams if team.name == team_name), None)

    # 2. Use a helper method from citrine.seeding.find_or_create, such as find_or_create_team.
    from citrine.seeding.find_or_create import find_or_create_team
    team_name = "Team A"
    team_a = find_or_create_team(team_collection=citrine.teams, team_name=team_name)

    # 3. If you have its unique ID, retrieve it directly.
    team_a = citrine.teams.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

Note that you can only retrieve a Team of which you are a member.

Managing Users
--------------

Admin users can manage permissions of Users in Teams. These replace the previous concept of roles.

There are three types of access permissions a user can have on a team: READ, SHARE, and WRITE.

- READ allows a user to view resources in a Team.
- WRITE allows them to modify those resources.
- SHARE allows them to publish those resources to other Teams.

There are several methods for managing teams, Users, and user membership in teams.


Listing Users in a Team
^^^^^^^^^^^^^^^^^^^^^^^^^^

Users in a Team can be listed using the :func:`~citrine.resources.team.Team.list_members` method.
The ``TeamMember`` array returned from this method has the user's access permissions in the Team
as well as a copy of the User and Team objects.

.. code-block:: python

     team = citrine.teams.register(name="Your Team")

     # List Members of a team
     team_members = team.list_members()

     # See their actions
     [(m.user.screen_name, m.actions) for m in team_members]
     # or
     [str(m) for m in team_members]


Add User to a Team
^^^^^^^^^^^^^^^^^^^^^

Users can be added to a Team. They will be granted READ access to resources in the Team.
This is accomplished with the :func:`~citrine.resources.team.Team.add_user` method.

.. code-block:: python

    # Get the UUID of the user you'd like to add
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    team = citrine.teams.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

    # Add them to your team
    team.add_user(user_id)

When adding a User to a Team, you can specify the actions that User should have:

.. code-block:: python

    from citrine.resources.team import READ, WRITE, SHARE
    # Add user to your team and give them read, write, and share permissions
    team.add_user(user_id, actions=[READ, WRITE, SHARE])


Remove User from a Team
^^^^^^^^^^^^^^^^^^^^^^^^^^

Users can also be removed from a Team. This is achieved with the
:func:`~citrine.resources.team.Team.remove_user` method.

.. code-block:: python

    # Get the UUID fo the user you'd like to delete
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    team = citrine.teams.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

    # Remove them from the team
    team.remove_user(user_id)


Update User's Actions in a Team
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A user's actions in a team can be updated. The method
:func:`~citrine.resources.team.Team.update_user_actions` facilitates changing a User's actions.


.. code-block:: python

    from citrine.resources.team import READ, WRITE
    user_id = "bed6f207-f15e-4aef-932d-87d99b2d6203"
    team = citrine.teams.get("baaa467e-1758-43a8-97c7-76e569d0dcab")

    # Make the user a member with read and write access
    team.update_user_actions(user_uid=user_id, actions=[READ, WRITE])
