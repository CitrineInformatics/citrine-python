# flake8: noqa
# The docstring includes many long links that violate flake8, and it's easier to noqa
# the whole file than to pick out the offending lines.
from typing import List, Optional

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as _properties
from citrine._utils.functions import migrate_deprecated_argument
from citrine.informatics.descriptors import Descriptor, MolecularStructureDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['MolecularStructureFeaturizer']


class MolecularStructureFeaturizer(VersionedEngineResource['MolecularStructureFeaturizer'], Predictor):
    """
    A featurizer for molecular structures, powered by CDK.

    The MolecularStructureFeaturizer will compute a configurable set of features on molecular
    structure data, e.g., SMILES or InChI strings.  The features are computed using the
    `Chemistry Development Kit (CDK) <https://cdk.github.io/>`_.  The features are configured
    using the ``features`` and ``excludes`` arguments, which accept either feature names or predefined
    aliases.

    The default is the `standard` alias, corresponding to eight features that are
    a good balance of cost and performance:

        - `AcidGroupCount  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AcidicGroupCountDescriptor.html>`_
        - `AtomCount  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/AtomContainer.html>`_
        - `AtomicPolarizability  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/charges/Polarizability.html>`_
        - `BondCount <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/AtomContainer.html>`_
        - `HBondAcceptorCount  <http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HBondAcceptorCountDescriptor.html>`_
        - `HBondDonorCount  <http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HBondDonorCountDescriptor.html>`_
        - `MassAutocorr  <http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AutocorrelationDescriptorMass.html>`_
        - `PolarizabilityAutocorr  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AutocorrelationDescriptorPolarizability.html>`_

    The ``extended`` alias includes more features that may improve model performance but are slower and may dilute the signal in the features.
    It includes the ``standard`` set and:

        - `ALOGP  <http://cdk.github.io/cdk/1.4/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ALOGPDescriptor.html>`_
        - `AromaticAtomCount  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/AromaticAtomsCountDescriptor.html>`_
        - `AromaticBondCount  <http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/aromaticity/Aromaticity.html>`_
        - `BasicGroupCount  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/BasicGroupCountDescriptor.html>`_
        - `BPol  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/BPolDescriptor.html>`_
        - `CarbonTypes  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/CarbonTypesDescriptor.html>`_
        - `EccentricConnectivityIndex  <http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/EccentricConnectivityIndexDescriptor.html>`_
        - `FMF  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FMFDescriptor.html>`_
        - `FragmentComplexity  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FragmentComplexityDescriptor.html>`_
        - `HybridizationRatioDescriptor  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/HybridizationRatioDescriptor.html>`_
        - `KappaShapeIndices  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/KappaShapeIndicesDescriptor.html>`_
        - `KierHallSmarts  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/KierHallSmartsDescriptor.html>`_
        - `LargestChain  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/LargestChainDescriptor.html>`_
        - `LargestPiSystem  <http://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/qsar/descriptors/molecular/LargestPiSystemDescriptor.html>`_
        - `MannholdLogP  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/MannholdLogPDescriptor.html>`_
        - `MDE  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/MDEDescriptor.html>`_
        - `PetitjeanNumber  <http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/PetitjeanNumberDescriptor.html>`_
        - `RotatableBondsCount  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/RotatableBondsCountDescriptor.html>`_
        - `RuleOfFive  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/RuleOfFiveDescriptor.html>`_
        - `TopologicalSurfaceArea  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/FractionalPSADescriptor.html>`_
        - `VertexAdjacencyMagnitude  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/VAdjMaDescriptor.html>`_
        - `Weight  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/WeightDescriptor.html>`_
        - `WienerNumbers  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/WienerNumbersDescriptor.html>`_
        - `XLogP  <https://cdk.github.io/cdk/1.5/docs/api/org/openscience/cdk/qsar/descriptors/molecular/XLogPDescriptor.html>`_
        - `ZagrebIndex  <http://cdk.github.io/cdk/latest/docs/api/org/openscience/cdk/qsar/descriptors/molecular/ZagrebIndexDescriptor.html>`_

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    descriptor: MolecularStructureDescriptor
        the descriptor to featurize
    features: List[str]
        the list of features to compute, either by name or by group alias.
    excludes: List[str]
        list of features to exclude (accepts same set of values as features). The final set
        of outputs generated by the predictor is set(features) - set(excludes).

    """

    input_descriptor = _properties.Object(Descriptor, 'data.instance.descriptor')
    features = _properties.List(_properties.String, 'data.instance.features')
    excludes = _properties.List(_properties.String, 'data.instance.excludes')

    typ = _properties.String('data.instance.type', default='MoleculeFeaturizer', deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: MolecularStructureDescriptor = None,
                 features: Optional[List[str]] = None,
                 excludes: Optional[List[str]] = None,
                 descriptor: MolecularStructureDescriptor = None):
        self.name: str = name
        self.description: str = description
        input_descriptor = migrate_deprecated_argument(
            input_descriptor, "input_descriptor", descriptor, "descriptor"
        )
        self.input_descriptor = input_descriptor
        self.features = features if features is not None else ["standard"]
        self.excludes = excludes if excludes is not None else []

    def __str__(self):
        return '<MolecularStructureFeaturizer {!r}>'.format(self.name)
