from typing import TypeVar

from citrine._rest.resource import Resource, ResourceTypeEnum


Self = TypeVar('Self', bound='Resource')


class PredictorResource(Resource[Self]):
    """Base resource for predictors."""

    _resource_type = ResourceTypeEnum.MODULE

    def _post_dump(self, data: dict) -> dict:
        # Only the data portion of a predictor entity is sent to the server.
        data = data["data"]

        # Currently, name and description exists on both the data envelope and the config.
        data["instance"]["name"] = data["name"]
        data["instance"]["description"] = data["description"]
        return data
