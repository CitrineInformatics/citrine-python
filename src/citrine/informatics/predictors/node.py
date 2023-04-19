import warnings
from datetime import datetime
from typing import Type, Optional, List
from uuid import UUID

from deprecation import deprecated

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine.informatics.data_sources import DataSource
from citrine.informatics.predictors import Predictor
from citrine.resources.status_detail import StatusDetail


def _check_deprecated_training_data(training_data: Optional[List[DataSource]]) -> None:
    if training_data is not None:
        warnings.warn(
            f"The field `training_data` on single predictor nodes is deprecated "
            "and will be removed in version 3.0.0. Include training data for all "
            "sub-predictors on the parent GraphPredictor. Existing training data "
            "on this predictor will be moved to the parent GraphPredictor upon registration.",
            DeprecationWarning
        )


class PredictorNode(PolymorphicSerializable["PredictorNode"], Predictor):
    """An individual compute node within a Predictor.

    A PredictorNode cannot be registered to the Citrine Platform by itself
    and must be included as a component within a GraphPredictor to be used.

    """

    name = properties.String("name")
    description = properties.Optional(properties.String(), "description")

    @classmethod
    def get_type(cls, data) -> Type['PredictorNode']:
        """Return the subtype."""
        from .expression_predictor import ExpressionPredictor
        from .molecular_structure_featurizer import MolecularStructureFeaturizer
        from .ingredients_to_formulation_predictor import IngredientsToFormulationPredictor
        from .label_fractions_predictor import LabelFractionsPredictor
        from .simple_mixture_predictor import SimpleMixturePredictor
        from .ingredient_fractions_predictor import IngredientFractionsPredictor
        from .auto_ml_predictor import AutoMLPredictor
        from .mean_property_predictor import MeanPropertyPredictor
        from .chemical_formula_featurizer import ChemicalFormulaFeaturizer
        type_dict = {
            "AnalyticExpression": ExpressionPredictor,
            "MoleculeFeaturizer": MolecularStructureFeaturizer,
            "IngredientsToSimpleMixture": IngredientsToFormulationPredictor,
            "MeanProperty": MeanPropertyPredictor,
            "LabelFractions": LabelFractionsPredictor,
            "SimpleMixture": SimpleMixturePredictor,
            "IngredientFractions": IngredientFractionsPredictor,
            "ChemicalFormulaFeaturizer": ChemicalFormulaFeaturizer,
            "AutoML": AutoMLPredictor,
        }
        typ = type_dict.get(data['type'])
        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor node type. '
                'Must be in {}.'.format(data['type'], type_dict.keys())
            )

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `uid` on parent GraphPredictor."
    )
    def uid(self) -> Optional[UUID]:
        """Optional Citrine Platform unique identifier."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `version` on parent GraphPredictor."
    )
    def version(self) -> Optional[int]:
        """The version number of the resource."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `draft` on parent GraphPredictor."
    )
    def draft(self) -> Optional[bool]:
        """The draft status of the resource."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `created_by` on parent GraphPredictor."
    )
    def created_by(self) -> Optional[UUID]:
        """The id of the user who created the resource."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `updated_by` on parent GraphPredictor."
    )
    def updated_by(self) -> Optional[UUID]:
        """The id of the user who most recently updated the resource."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `archived_by` on parent GraphPredictor."
    )
    def archived_by(self) -> Optional[UUID]:
        """The id of the user who most recently archived the resource."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `create_time` on parent GraphPredictor."
    )
    def create_time(self) -> Optional[datetime]:
        """The date and time at which the resource was created."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `update_time` on parent GraphPredictor."
    )
    def update_time(self) -> Optional[datetime]:
        """The date and time at which the resource was most recently updated."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Use `archive_time` on parent GraphPredictor."
    )
    def archive_time(self) -> Optional[datetime]:
        """The date and time at which the resource was archived."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Check `status` on parent GraphPredictor."
    )
    def status(self) -> Optional[str]:
        """Short description of the resource's status."""
        return None

    @property
    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Check `status_detail` on parent GraphPredictor."
    )
    def status_detail(self) -> List[StatusDetail]:
        """A list of structured status info, containing the message and level."""
        return []

    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Check `in_progress` on parent GraphPredictor."
    )
    def in_progress(self) -> bool:
        """Whether the backend process is in progress."""
        return False

    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Check `succeeded` on parent GraphPredictor."
    )
    def succeeded(self) -> bool:
        """Whether the backend process has completed successfully."""
        return False

    @deprecated(
        deprecated_in="2.13.0",
        removed_in="3.0.0",
        details="Check `failed` on parent GraphPredictor."
    )
    def failed(self) -> bool:
        """Whether the backend process has completed unsuccessfully."""
        return False
