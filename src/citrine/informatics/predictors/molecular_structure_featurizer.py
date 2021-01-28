# flake8: noqa
# The docstring includes many long links that violate flake8, and it's easier to noqa
# the whole file than to pick out the offending lines.
from typing import List, Optional

from citrine._serialization import properties as _properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor, MolecularStructureDescriptor
from citrine.informatics.reports import Report
from citrine.informatics.predictors import Predictor

__all__ = ['MolecularStructureFeaturizer']


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

    descriptor = _properties.Object(Descriptor, 'config.descriptor')
    features = _properties.List(_properties.String, 'config.features')
    excludes = _properties.List(_properties.String, 'config.excludes')
    typ = _properties.String('config.type', default='MoleculeFeaturizer', deserializable=False)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = _properties.String('module_type', default='PREDICTOR')

    def __init__(self,
                 name: str,
                 description: str,
                 descriptor: MolecularStructureDescriptor,
                 features: List[str] = None,
                 excludes: List[str] = None,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 archived: bool = False):
        self.name: str = name
        self.description: str = description
        self.descriptor = descriptor
        self.features = features if features is not None else ["standard"]
        self.excludes = excludes if excludes is not None else []
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.archived: bool = archived

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<MolecularStructureFeaturizer {!r}>'.format(self.name)
