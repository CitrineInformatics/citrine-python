from typing import Optional

from citrine.resources.team import Team, TeamCollection


class FakeTeam(Team):

    def __init__(self, name):
        self.name = name


class FakeTeamCollection(TeamCollection):

    def __init__(self, session):
        TeamCollection.__init__(self, session=session)
        self.teams = []

    def register(self, name: str) -> Team:
        model = FakeTeam(name)
        self.teams.append(model)
        return model

    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return self.teams
        else:
            return self.teams[(page - 1) * per_page:page * per_page]
