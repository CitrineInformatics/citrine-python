from typing import Union
from uuid import uuid4, UUID

from citrine.exceptions import BadRequest
from citrine.informatics.design_spaces import DesignSpace
from citrine.resources.design_space import DesignSpaceCollection


class FakeDesignSpaceCollection(DesignSpaceCollection):
    def __init__(self):
        self.data = {}
        self.in_use = {}

    def register(self, model: DesignSpace) -> DesignSpace:
        model.uid = uuid4()
        self.data[model.uid] = model
        self.in_use[model.uid] = False
        return model

    def update(self, model: DesignSpace) -> DesignSpace:
        if self.in_use[model.uid]:
            raise BadRequest("design_spaces/{}".format(model.uid))
        self.data[model.uid] = model
        return model

    def get(self, uid: Union[UUID, str]) -> DesignSpace:
        return self.data[uid]
