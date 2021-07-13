from typing import Tuple, List, Optional, Union

from citrine.resources.project import Project
from citrine.informatics.predictors import (
    MolecularStructureFeaturizer,
    ChemicalFormulaFeaturizer,
    MeanPropertyPredictor
)
from citrine.informatics.descriptors import Descriptor, FormulationDescriptor, RealDescriptor


def build_mean_feature_property_predictors(
        *,
        project: Project,
        featurizer: Union[MolecularStructureFeaturizer, ChemicalFormulaFeaturizer],
        formulation_descriptor: FormulationDescriptor,
        p: int,
        impute_properties: bool = True,
        make_all_ingredients_model: bool = True,
        labels: Optional[List[str]] = None
) -> Tuple[List[MeanPropertyPredictor], List[Descriptor]]:
    """[ALPHA] Combine a featurizer model with mean property models.

    Given a featurizer, produce "mean property" models that calculate the mean of the
    properties calculated by the featurizer. This is useful if you do not directly know
    the numerical properties of ingredients in a formulation, but instead know, for example,
    the molecular structure. This builder method determines the real-valued properties that the
    featurizer calculates and builds mean property models that use them as input properties.

    Parameters
    ----------
    project: Project
        Project that contains the predictor
    featurizer: Union[MolecularStructureFeaturizer, ChemicalFormulaFeaturizer]
        A model that is being used to featurize formulation ingredients. Currently only
        accepts a molecular structure featurizer or a chemical formula featurizer.
    formulation_descriptor: FormulationDescriptor
        Descriptor that represents the formulation being featurized.
    p: int
        Power of the generalized mean. Only integer powers are supported.
    impute_properties: bool
        Whether to impute missing ingredient properties by averaging over the entire dataset.
        If ``False`` all ingredients must define values for all featurized properties.
        Otherwise, the row will not be featurized.
    make_all_ingredients_model: bool
        Whether to create a mean property predictor that calculates the mean over all ingredients.
        If False, models are only constructed for specified labels. Must be True if no labels
        are specified.
    labels: Optional[List[str]]
        List of labels for which a mean property predictor should be created.

    Returns
    -------
    Tuple[List[MeanPropertyPredictor], List[Descriptor]]
        List of mean property predictors that should be incorporated into the graph predictor,
        and a list of all the output descriptors produced by these models. There will be one
        model for each label specified, and one model for all ingredients if ``all_ingredients``
        is set to ``True``. In the common case, the output descriptors will all be used
        as inputs to one or more ML models.

    """
    if isinstance(featurizer, (MolecularStructureFeaturizer, ChemicalFormulaFeaturizer)):
        input_descriptor = featurizer.input_descriptor
    else:
        raise TypeError(f"Featurizer of type {type(featurizer)} is not supported.")

    if labels is None:
        labels = []
    if not isinstance(labels, (list, set)):
        raise TypeError("labels must be specified as a list or set of strings.")
    if make_all_ingredients_model:
        labels = [None] + labels
    if len(labels) == 0:
        msg = "No mean property predictors requested. " \
              "Set make_all_ingredients_model to True and/or specify labels."
        raise ValueError(msg)

    properties = project.descriptors.from_predictor_responses(
        predictor=featurizer, inputs=[input_descriptor]
    )
    real_properties = [desc for desc in properties if isinstance(desc, RealDescriptor)]
    if len(real_properties) == 0:
        msg = "Featurizer did not return any real properties to calculate the means of."
        raise RuntimeError(msg)

    predictors = [
        _build_mean_property_predictor(
            ingredient_descriptor=input_descriptor,
            formulation_descriptor=formulation_descriptor,
            properties=real_properties,
            p=p,
            impute_properties=impute_properties,
            label=label
        )
        for label in labels
    ]

    all_outputs = [
        output
        for single_model_outputs in [
            project.descriptors.from_predictor_responses(
                predictor=predictor, inputs=[formulation_descriptor]
            )
            for predictor in predictors
        ]
        for output in single_model_outputs
    ]

    return predictors, all_outputs


def _build_mean_property_predictor(
        ingredient_descriptor: Descriptor,
        formulation_descriptor: FormulationDescriptor,
        properties: List[RealDescriptor],
        p: int,
        impute_properties: bool,
        label: Optional[str]
) -> MeanPropertyPredictor:
    """Build a MeanPropertyPredictor for given specifications."""
    name = f"mean of {ingredient_descriptor.key} features"
    if p != 1:
        name = f"{p}-{name}"
    if label is not None:
        name += f" for label {label}"
    name += f" in {formulation_descriptor.key}"

    return MeanPropertyPredictor(
        name=name,
        description="",
        input_descriptor=formulation_descriptor,
        properties=properties,
        p=p,
        impute_properties=impute_properties,
        label=label
    )
