"""Tools for working with Predictors."""
# flake8: noqa
from typing import Dict, List, Optional, Type, Union
from uuid import UUID

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor, FormulationDescriptor, RealDescriptor, \
    MolecularStructureDescriptor
from citrine.informatics.reports import Report
from citrine.resources.report import ReportResource
from citrine.informatics.modules import Module

__all__ = ['ExpressionPredictor',
           'GraphPredictor',
           'IngredientsToSimpleMixturePredictor',
           'Predictor',
           'SimpleMLPredictor',
           'MolecularStructureFeaturizer',
           'GeneralizedMeanPropertyPredictor',
           'LabelFractionsPredictor',
           'SimpleMixturePredictor',
           'IngredientFractionsPredictor']


class Predictor(Module):
    """[ALPHA] Module that describes the ability to compute/predict properties of materials.

    Abstract type that returns the proper type given a serialized dict. subtype
    based on the 'type' value of the passed in dict.

    """

    _response_key = None

    def post_build(self, project_id: UUID, data: dict):
        """Executes after a .build() is called in [[PredictorCollection]]."""
        self.report = ReportResource(project_id, self.session).get(data['id'])

    @classmethod
    def get_type(cls, data) -> Type['Predictor']:
        """Return the subtype."""
        type_dict = {
            "Simple": SimpleMLPredictor,
            "Graph": GraphPredictor,
            "Expression": ExpressionPredictor,
            "MoleculeFeaturizer": MolecularStructureFeaturizer,
            "IngredientsToSimpleMixture": IngredientsToSimpleMixturePredictor,
            "GeneralizedMeanProperty": GeneralizedMeanPropertyPredictor,
            "LabelFractions": LabelFractionsPredictor,
            "SimpleMixture": SimpleMixturePredictor,
            "IngredientFractions": IngredientFractionsPredictor,
        }
        typ = type_dict.get(data['config']['type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor type. '
                'Must be in {}.'.format(data['config']['type'], type_dict.keys())
            )


class SimpleMLPredictor(Serializable['SimplePredictor'], Predictor):
    """[ALPHA] A predictor interface that builds a simple graphical model.

    The model connects the set of inputs through latent variables to the outputs.
    Supported complex inputs (such as chemical formulas) are auto-featurized and machine learning
    models are built for each latent variable and output.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    inputs: list[Descriptor]
        Descriptors that represent inputs to relations
    outputs: list[Descriptor]
        Descriptors that represent outputs of relations
    latent_variables: list[Descriptor]
        Descriptors that are predicted from inputs and used when predicting the outputs
    training_data: DataSource
        Source of the training data, which can be either a CSV or an Ara table

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.Optional(_properties.String(), 'config.description')
    inputs = _properties.List(_properties.Object(Descriptor), 'config.inputs')
    outputs = _properties.List(_properties.Object(Descriptor), 'config.outputs')
    latent_variables = _properties.List(_properties.Object(Descriptor), 'config.latent_variables')
    training_data = _properties.Object(DataSource, 'config.training_data')
    typ = _properties.String('config.type', default='Simple', deserializable=False)
    status = _properties.Optional(_properties.String(), 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String()),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('08d20e5f-e329-4de0-a90a-4b5e36b91703'))

    def __init__(self,
                 name: str,
                 description: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 latent_variables: List[Descriptor],
                 training_data: DataSource,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.outputs: List[Descriptor] = outputs
        self.latent_variables: List[Descriptor] = latent_variables
        self.training_data: DataSource = training_data
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<SimplePredictor {!r}>'.format(self.name)


class GraphPredictor(Serializable['GraphPredictor'], Predictor):
    """[ALPHA] A predictor interface that stitches other predictors together.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: list[UUID, Predictor]
        the list of predictors to use in the grpah, either UUIDs or serialized predictors

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    predictors = _properties.List(_properties.Union(
        [_properties.UUID, _properties.Object(Predictor)]), 'config.predictors')
    typ = _properties.String('config.type', default='Graph', deserializable=False)
    # Graph predictors may not be embedded in other predictors, hence while status is optional
    # for deserializing most predictors, it is required for deserializing a graph
    status = _properties.String('status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String()),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('43c61ad4-7e33-45d0-a3de-504acb4e0737'))

    def __init__(self,
                 name: str,
                 description: str,
                 predictors: List[Union[UUID, Predictor]],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.predictors: List[Union[UUID, Predictor]] = predictors
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                # embedded predictors are not modules, so only serialize their config
                data['config']['predictors'][i] = predictor['config']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                data['config']['predictors'][i] = \
                    GraphPredictor.stuff_predictor_into_envelope(predictor)
        return data

    @staticmethod
    def stuff_predictor_into_envelope(predictor: dict) -> dict:
        """Insert a serialized embedded predictor into a module envelope, to facilitate deser."""
        return dict(
            module_type='PREDICTOR',
            config=predictor,
            active=False,
            schema_id='43c61ad4-7e33-45d0-a3de-504acb4e0737'  # TODO: what should this be?
        )

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)


class ExpressionPredictor(Serializable['ExpressionPredictor'], Predictor):
    """[ALPHA] A predictor interface that allows calculator expressions.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    expression: str
        the expression that uses the aliased values
    output: Descriptor
        the Descriptor that represents the output relation
    aliases: dict
        a mapping from expression argument to descriptor key

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    expression = _properties.String('config.expression')
    output = _properties.Object(Descriptor, 'config.output')
    aliases = _properties.Mapping(_properties.String, _properties.String, 'config.aliases')
    typ = _properties.String('config.type', default='Expression', deserializable=False)
    status = _properties.Optional(_properties.String(), 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String()),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('866e72a6-0a01-4c5f-8c35-146eb2540166'))

    def __init__(self,
                 name: str,
                 description: str,
                 expression: str,
                 output: Descriptor,
                 aliases: dict,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.expression: str = expression
        self.output: Descriptor = output
        self.aliases: dict = aliases
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ExpressionPredictor {!r}>'.format(self.name)


class MolecularStructureFeaturizer(Serializable['MolecularStructureFeaturizer'], Predictor):
    """
    [ALPHA] A "batteries-included" featurizer for organic molecules. Powered by CDK.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    descriptor: MolecularStructureDescriptor
        the descriptor to featurize
    features: List[str]
        the list of features to compute (first 3 are aliases for feature sets).
        Valid values include:
        - all (alias for all below)
        - standard (alias for AcidGroupCount, AtomicPolarizability, MassAutocorr,
        PolarizabilityAutocorr, HBondAcceptorCount, BondCount, and AtomCount)
        - expensive (alias for WeightedPath, ChiChain, ChiCluster, ChiPathCluster, and ChiPath)
        - TopologicalSurfaceArea `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FractionalPSADescriptor.html>`
        - EccentricConnectivityIndex `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/EccentricConnectivityIndexDescriptor.html>`
        - KappaShapeIndices `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/KappaShapeIndicesDescriptor.html>`
        - RuleOfFive `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/RuleOfFiveDescriptor.html>`
        - ALOGP `CDK Link<http://cdk.github.io/cdk/1.4/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ALOGPDescriptor.html>`
        - PolarizabilityAutocorr `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AutocorrelationDescriptorPolarizability.html>`
        - BondCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/AtomContainer.html>`
        - VertexAdjacencyMagnitude `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/VAdjMaDescriptor.html>`
        - ZagrebIndex `CDK Link<http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ZagrebIndexDescriptor.html>`
        - HBondDonorCount `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HBondDonorCountDescriptor.html>`
        - ChiPathCluster `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ChiPathClusterDescriptor.html>`
        - MannholdLogP `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/MannholdLogPDescriptor.html>`
        - AtomCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/AtomContainer.html>`
        - AromaticAtomCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AromaticAtomsCountDescriptor.html>`
        - LargestPiSystem `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/LargestPiSystemDescriptor.html>`
        - HybridizationRatioDescriptor `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HybridizationRatioDescriptor.html>`
        - LargestChain `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/LargestChainDescriptor.html>`
        - MDE `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/MDEDescriptor.html>`
        - Weight `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/WeightDescriptor.html>`
        - FMF `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FMFDescriptor.html>`
        - AtomicPolarizability `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/charges/Polarizability.html>`
        - CarbonTypes `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/CarbonTypesDescriptor.html>`
        - PetitjeanNumber `CDK Link<http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/PetitjeanNumberDescriptor.html>`
        - HBondAcceptorCount `CDK Link<http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HBondAcceptorCountDescriptor.html>`
        - RotatableBondsCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/RotatableBondsCountDescriptor.html>`
        - WeightedPath `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/WeightedPathDescriptor.html>`
        - AromaticBondCount `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/aromaticity/Aromaticity.html>`
        - XLogP `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/XLogPDescriptor.html>`
        - ChiPath `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ChiPathDescriptor.html>`
        - FragmentComplexity `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FragmentComplexityDescriptor.html>`
        - ChiChain `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ChiChainDescriptor.html>`
        - KierHallSmarts `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/KierHallSmartsDescriptor.html>`
        - MassAutocorr `CDK Link<http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AutocorrelationDescriptorMass.html>`
        - AcidGroupCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AcidicGroupCountDescriptor.html>`
        - BPol `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/BPolDescriptor.html>`
        - WienerNumbers `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/WienerNumbersDescriptor.html>`
        - ChiCluster `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ChiClusterDescriptor.html>`
        - BasicGroupCount `CDK Link<https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/BasicGroupCountDescriptor.html>`
    excludes: List[str]
        list of features to exclude (accepts same set of values as features). The final set
        of outputs generated by the predictor is set(features) - set(excludes).

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    descriptor = _properties.Object(Descriptor, 'config.descriptor')
    features = _properties.List(_properties.String, 'config.features')
    excludes = _properties.List(_properties.String, 'config.excludes')
    typ = _properties.String('config.type', default='MoleculeFeaturizer', deserializable=False)
    status = _properties.Optional(_properties.String, 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('24183b2f-848c-46fa-8640-21b7743e38a3'))

    def __init__(self,
                 name: str,
                 description: str,
                 descriptor: MolecularStructureDescriptor,
                 features: List[str] = None,
                 excludes: List[str] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.descriptor = descriptor
        self.features = features if features is not None else ["standard"]
        self.excludes = excludes if excludes is not None else []
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<MolecularStructureFeaturizer {!r}>'.format(self.name)


class IngredientsToSimpleMixturePredictor(
        Serializable['IngredientsToSimpleMixturePredictor'], Predictor):
    """[ALPHA] A predictor interface that constructs a simple mixture from ingredient quantities.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    output: FormulationDescriptor
        descriptor that represents the output formulation
    id_to_quantity: Dict[str, RealDescriptor]
        Map from ingredient identifier to the descriptor that represents its quantity,
        e.g. ``{'water': RealDescriptor('water quantity', 0, 1)}``
    labels: Dict[str, List[str]]
        Map from each label to all ingredients assigned that label, when present in a mixture,
        e.g. ``{'solvent': ['water']}``

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    output = _properties.Object(FormulationDescriptor, 'config.output')
    id_to_quantity = _properties.Mapping(_properties.String, _properties.Object(RealDescriptor),
                                         'config.id_to_quantity')
    labels = _properties.Mapping(_properties.String, _properties.List(_properties.String),
                                 'config.labels')
    typ = _properties.String('config.type', default='IngredientsToSimpleMixture',
                             deserializable=False)
    status = _properties.Optional(_properties.String(), 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String()),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('873e4541-da8a-4698-a981-732c0c729c3d'))

    def __init__(self,
                 name: str,
                 description: str,
                 output: FormulationDescriptor,
                 id_to_quantity: Dict[str, RealDescriptor],
                 labels: Dict[str, List[str]],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.output: FormulationDescriptor = output
        self.id_to_quantity: Dict[str, RealDescriptor] = id_to_quantity
        self.labels: Dict[str, List[str]] = labels
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<IngredientsToSimpleMixturePredictor {!r}>'.format(self.name)


class GeneralizedMeanPropertyPredictor(
        Serializable['GeneralizedMeanPropertyPredictor'], Predictor):
    """[ALPHA] A predictor interface that computes generalized mean component properties.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    properties: List[str]
        List of component properties to featurize
    p: float
        Power of the generalized mean
    impute_properties: bool
        Whether to impute missing ingredient properties.
        If ``False`` an error is thrown when a missing ingredient property is encountered.
        If ``True`` and no ``default_properties`` are specified, then the average over the
        entire dataset is used.
        If ``True`` and a default is specified in ``default_properties``, then the specified
        default is used in place of missing values.
    training_data: DataSource
        Source of the training data, which can be either a CSV or an Ara table
    label: Optional[str]
        Optional label
    default_properties: Optional[Dict[str, float]]
        Default values to use for imputed properties.
        Defaults are specified as a map from descriptor key to its default value.
        If not specified and ``impute_properties == True`` the average over the entire dataset
        will be used to fill in missing values. Any specified defaults will be used in place of
        the average over the dataset. ``impute_properties`` must be ``True`` if
        ``default_properties`` are provided.

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    properties = _properties.List(_properties.String, 'config.properties')
    p = _properties.Float('config.p')
    training_data = _properties.Object(DataSource, 'config.training_data')
    impute_properties = _properties.Boolean('config.impute_properties')
    default_properties = _properties.Optional(
        _properties.Mapping(_properties.String, _properties.Float), 'config.default_properties')
    label = _properties.Optional(_properties.String, 'config.label')
    typ = _properties.String('config.type', default='GeneralizedMeanProperty',
                             deserializable=False)
    status = _properties.Optional(_properties.String, 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('29e53222-3217-4f81-b3b8-4197a8211ade'))

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 properties: List[str],
                 p: float,
                 training_data: DataSource,
                 impute_properties: bool,
                 default_properties: Optional[Dict[str, float]] = None,
                 label: Optional[str] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.properties: List[str] = properties
        self.p: float = p
        self.training_data = training_data
        self.impute_properties: bool = impute_properties
        self.default_properties: Optional[Dict[str, float]] = default_properties
        self.label: Optional[str] = label
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<GeneralizedMeanPropertyPredictor {!r}>'.format(self.name)


class SimpleMixturePredictor(Serializable['SimpleMixturePredictor'], Predictor):
    """
    [ALPHA] A predictor interface that builds a simple graphical model.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        input descriptor for the hierarchical (un-mixed) formulation
    output_descriptor: FormulationDescriptor
        output descriptor for the flat (mixed) formulation
    training_data: DataSource
        Source of the training data, which can be either a CSV or an Ara table

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    output_descriptor = _properties.Object(FormulationDescriptor, 'config.output')
    training_data = _properties.Object(DataSource, 'config.training_data')
    typ = _properties.String('config.type', default='SimpleMixture',
                             deserializable=False)
    status = _properties.Optional(_properties.String, 'status', serializable=False)
    status_info = _properties.Optional(_properties.List(_properties.String),
                                       'status_info',
                                       serializable=False)
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('e82a993c-e6ab-46a2-b636-c71d0ba224d1'))

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 output_descriptor: FormulationDescriptor,
                 training_data: DataSource,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.output_descriptor: FormulationDescriptor = output_descriptor
        self.training_data = training_data
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<SimpleMixturePredictor {!r}>'.format(self.name)


class LabelFractionsPredictor(Serializable['LabelFractionsPredictor'], Predictor):
    """[ALPHA] A predictor interface that computes the relative proportions of labeled ingredients.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that contains formulation data
    labels: List[str]
        labels to compute the quantity fractions of

    """

    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    labels = _properties.List(_properties.String, 'config.labels')
    typ = _properties.String('config.type', default='LabelFractions',
                             deserializable=False)
    status = _properties.Optional(_properties.String, 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('997a7e11-2c16-4e30-b531-9e657a863019'))

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 labels: List[str],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.labels: List[str] = labels
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<LabelFractionsPredictor {!r}>'.format(self.name)


class IngredientFractionsPredictor(Serializable["IngredientFractionsPredictor"], Predictor):
    """[ALPHA] A predictor interface that computes ingredient fractions.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    input_descriptor: FormulationDescriptor
        descriptor that represents the input formulation
    ingredients: List[str]
        list of ingredients to featurize.
        This list should contain all possible ingredients.
        If an unknown ingredient is encountered, an error will be thrown.
    """
    uid = _properties.Optional(_properties.UUID, 'id', serializable=False)
    name = _properties.String('config.name')
    description = _properties.String('config.description')
    input_descriptor = _properties.Object(FormulationDescriptor, 'config.input')
    ingredients = _properties.List(_properties.String, 'config.ingredients')

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')
    schema_id = _properties.UUID('schema_id', default=UUID('eb02a095-8cdc-45d8-bc82-1013b6e8e700'))
    typ = _properties.String('config.type', default='IngredientFractions',
                             deserializable=False)
    status = _properties.Optional(_properties.String, 'status', serializable=False)
    status_info = _properties.Optional(
        _properties.List(_properties.String),
        'status_info',
        serializable=False
    )
    active = _properties.Boolean('active', default=True)

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: FormulationDescriptor,
                 ingredients: List[str],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.input_descriptor: FormulationDescriptor = input_descriptor
        self.ingredients: List[str] = ingredients
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<IngredientFractionsPredictor {!r}>'.format(self.name)
