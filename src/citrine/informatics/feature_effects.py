from typing import Dict
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties


class ShapleyMaterial(Resource):
    """The feature effect of a material."""

    material_id = properties.UUID("material_id", serializable=False)
    value = properties.Float("value", serializable=False)


class ShapleyFeature(Resource):
    """All feature effects for this feature by material."""

    feature = properties.String("feature", serializable=False)
    materials = properties.List(
        properties.Object(ShapleyMaterial), "materials", serializable=False
    )

    @property
    def material_dict(self) -> Dict[UUID, float]:
        """Presents the feature's effects as a dictionary by material."""
        return {material.material_id: material.value for material in self.materials}


class ShapleyOutput(Resource):
    """All feature effects for this output by feature."""

    output = properties.String("output", serializable=False)
    features = properties.List(
        properties.Object(ShapleyFeature), "features", serializable=False
    )

    @property
    def feature_dict(self) -> Dict[str, Dict[UUID, float]]:
        """Presents the output's feature effects as a dictionary by feature."""
        return {feature.feature: feature.material_dict for feature in self.features}


class FeatureEffects(Resource):
    """Captures information about the feature effects associated with a predictor."""

    predictor_id = properties.UUID("metadata.predictor_id", serializable=False)
    predictor_version = properties.Integer(
        "metadata.predictor_version", serializable=False
    )
    status = properties.String("metadata.status", serializable=False)
    failure_reason = properties.Optional(
        properties.String(), "metadata.failure_reason", serializable=False
    )

    outputs = properties.Optional(
        properties.List(properties.Object(ShapleyOutput)),
        "resultobj",
        serializable=False,
    )

    @classmethod
    def _pre_build(cls, data: dict) -> Dict:
        shapley = data.get("result")
        if not shapley:
            return data

        material_ids = shapley["materials"]

        outputs = []
        for output, feature_dict in shapley["outputs"].items():
            features = []
            for feature, values in feature_dict.items():
                items = zip(material_ids, values)
                materials = [
                    {"material_id": mid, "value": value} for mid, value in items
                ]
                features.append({"feature": feature, "materials": materials})

            outputs.append({"output": output, "features": features})

        data["resultobj"] = outputs
        return data

    @property
    def as_dict(self) -> Dict[str, Dict[str, Dict[UUID, float]]]:
        """Presents the feature effects as a dictionary by output."""
        if self.outputs:
            return {output.output: output.feature_dict for output in self.outputs}
        else:
            return {}
