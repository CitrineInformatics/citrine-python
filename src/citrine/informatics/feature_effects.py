"""Feature importance via Shapley values for trained predictors.

Shapley values quantify how much each input feature
contributes to a predictor's output for each material in the
training set. Positive values indicate the feature pushes the
prediction higher; negative values push it lower. The
magnitude reflects the strength of the effect.

Access feature effects via
:attr:`~citrine.informatics.predictors.graph_predictor.GraphPredictor.feature_effects`.

The class hierarchy is:

* :class:`FeatureEffects` — top level, one per predictor
* :class:`ShapleyOutput` — one per predicted output
* :class:`ShapleyFeature` — one per input feature
* :class:`ShapleyMaterial` — one per training material

"""
from typing import Dict
from uuid import UUID

from citrine._rest.resource import Resource
from citrine._serialization import properties


class ShapleyMaterial(Resource):
    """Shapley value for one material and one feature.

    Attributes
    ----------
    material_id : UUID
        Identifier of the training material.
    value : float
        Shapley value. Positive means the feature pushes
        the prediction higher; negative means lower.

    """

    material_id = properties.UUID('material_id', serializable=False)
    value = properties.Float('value', serializable=False)


class ShapleyFeature(Resource):
    """Shapley values for one input feature across all materials.

    Attributes
    ----------
    feature : str
        Name of the input feature.
    materials : list[ShapleyMaterial]
        Shapley values for each training material.

    """

    feature = properties.String('feature', serializable=False)
    materials = properties.List(properties.Object(ShapleyMaterial), 'materials',
                                serializable=False)

    @property
    def material_dict(self) -> Dict[UUID, float]:
        """Presents the feature's effects as a dictionary by material."""
        return {material.material_id: material.value for material in self.materials}


class ShapleyOutput(Resource):
    """Shapley values for one predicted output, grouped by feature.

    Attributes
    ----------
    output : str
        Name of the predicted output.
    features : list[ShapleyFeature]
        Shapley values broken down by input feature.

    """

    output = properties.String('output', serializable=False)
    features = properties.List(properties.Object(ShapleyFeature), 'features', serializable=False)

    @property
    def feature_dict(self) -> Dict[str, Dict[UUID, float]]:
        """Presents the output's feature effects as a dictionary by feature."""
        return {feature.feature: feature.material_dict for feature in self.features}


class FeatureEffects(Resource):
    """Feature importance results for a trained predictor.

    Contains Shapley values showing how each input feature
    affects each predicted output for every material in the
    training set. Use :attr:`as_dict` for a convenient nested
    dictionary representation.

    Attributes
    ----------
    predictor_id : UUID
        The predictor these results belong to.
    predictor_version : int
        The predictor version that was analyzed.
    status : str
        Computation status (e.g. ``'Succeeded'``).
    failure_reason : str or None
        Reason for failure, if status is not succeeded.
    outputs : list[ShapleyOutput] or None
        The computed Shapley values, grouped by output.

    """

    predictor_id = properties.UUID('metadata.predictor_id', serializable=False)
    predictor_version = properties.Integer('metadata.predictor_version', serializable=False)
    status = properties.String('metadata.status', serializable=False)
    failure_reason = properties.Optional(properties.String(), 'metadata.failure_reason',
                                                              serializable=False)

    outputs = properties.Optional(properties.List(properties.Object(ShapleyOutput)), 'resultobj',
                                  serializable=False)

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
                materials = [{"material_id": mid, "value": value} for mid, value in items]
                features.append({
                    "feature": feature,
                    "materials": materials
                })

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
