from typing import List, Optional

from citrine._rest.engine_resource import VersionedEngineResource
from citrine._serialization import properties as _properties
from citrine.informatics.descriptors import ChemicalFormulaDescriptor, Descriptor
from citrine.informatics.predictors import Predictor

__all__ = ['ChemicalFormulaFeaturizer']


class ChemicalFormulaFeaturizer(VersionedEngineResource['ChemicalFormulaFeaturizer'], Predictor):
    """
    A featurizer for chemical formulae. Inspired by Magpie.

    The ChemicalFormulaFeaturizer computes a configurable set of features on chemical formula data.
    The features are functions of element-level properties, which are inspired by
    `Magpie <https://bitbucket.org/wolverton/magpie/src/master/>`_. The features are configured
    using the ``features`` and ``excludes`` arguments, which accept either feature names or
    predefined aliases. Many features are stoichiometrically weighted generalized means of
    element-level properties. How to compute the mean is configured using the ``powers`` argument.

    The default is the "standard" alias, corresponding to features that are intuitive and
    often correlate with properties of interest. Other aliases are "physical," "electronic,"
    and "periodicTable."

    The following features are weighted means of simple elemental properties.

    - "Pauling electronegativity": standard, electronic
    - "Number of d valence electrons": standard, electronic
    - "Number of unfilled f valence electrons": standard, electronic
    - "Number of f valence electrons": standard, electronic
    - "Number of unfilled p valence electrons": standard, electronic
    - "Number of p valence electrons": standard, electronic
    - "Number of unfilled s valence electrons": standard, electronic
    - "Number of s valence electrons": standard, electronic
    - "Total number of unfilled valence electrons": standard, electronic
    - "Total number of valence electrons": standard, electronic
    - "Elemental work function": standard, electronic
    - "Elemental polarizability": standard, electronic
    - "Radius of d orbitals": standard, electronic
    - "Radius of s orbitals": standard, electronic
    - "Radius of p orbitals": standard, electronic
    - "Elemental magnetic moment": standard, electronic
    - "Elemental atomic volume": standard, electronic, physical
    - "Elemental electron density": standard, electronic
    - "Mendeleev number": standard, periodicTable
    - "Row in periodic table": standard, periodicTable
    - "Elemental bulk modulus": standard, physical
    - "Elemental density": standard, physical
    - "Elemental melting temperature": standard, physical
    - "Elemental crystal structure (space group)": standard, electronic, physical
    - "AtomicVolume": electronic, physical
    - "Number": periodicTable
    - "CovalentRadius": electronic, physical
    - "DipolePolarizability": electronic
    - "ElectronAffinity": electronic
    - "FirstIonizationEnergy": electronic
    - "GSbandgap": electronic
    - "GSenergy_pa": electronic
    - "GSestBCClatcnt": electronic, physical
    - "GSvolume_pa": electronic, physical
    - "MiracleRadius": electronic, physical
    - "NdUnfilled": electronic
    - "ZungerPP-r_pi": electronic
    - "AtomicWeight": physical, periodicTable
    - "Column in periodic table": periodicTable
    - "IsAlkali": periodicTable
    - "IsDBlock": periodicTable
    - "IsFBlock": periodicTable
    - "IsMetal": periodicTable
    - "IsNonmetal": periodicTable
    - "BoilingT": physical
    - "FusionEnthalpy": physical
    - "HeatCapacityMass": physical
    - "HeatCapacityMolar": physical
    - "HeatFusion": physical
    - "ShearModulus": physical
    - "ValenceZeff": electronic, physical

    The following features are weighted means of more complex elemental properties.

    - "Packing density": standard, physical
    - "Liquid range": standard, physical
    - "Non-dimensional liquid range": standard, physical
    - "Liquid ratio": standard, physical
    - "Elastic Poisson Ratio": standard, physical
    - "DFT energy density": standard, electronic, physical
    - "Interatomic distance": standard, physical
    - "Ionization Affinity Ratio": standard, electronic
    - "Ratio of Electron Affinity to Electronegativity": standard, electronic
    - "Trouton's Ratio": standard, physical
    - "Miracle Ratio": standard, electronic
    - "DFT volume ratio": standard, physical
    - "Mulliken electronegativity": standard, electronic
    - "Modulii sum": standard, physical
    - "Zunger Pseudopotential radius ratio": standard, electronic
    - "BCC Efficiency": standard, physical
    - "Non-dimensional heat of fusion": standard, physical
    - "Non-dimensional band gap": standard, electronic
    - "Conduction ionization energy": standard, electronic
    - "Valence electron density": standard, electronic
    - "Non-dimensional work function": standard, electronic
    - "Shear Modulus Melting Temp Product": standard, physical

    The following features are not weighted means. Their values do not depend on ``powers``.

    - "Maximum electronegativity difference": standard, electronic
    - "Maximum radius difference": standard, electronic, physical
    - "Maximum radius ratio": standard, electronic, physical
    - "Min atomic radius plus max electronegativity difference": standard, electronic, physical
    - "Number of elements"
    - "Minimum atomic fraction"
    - "Maximum atomic fraction"
    - "Minimum weight fraction": standard, periodicTable
    - "Maximum weight fraction": standard, periodicTable
    - "Formula weight": standard, physical

    Parameters
    ----------
    input_descriptor: ChemicalFormulaDescriptor
        the descriptor to featurize
    features: Optional[List[str]]
        The list of features to compute, either by name or by group alias. Default is "standard."
    excludes: Optional[List[str]]
        The list of features to exclude, either by name or by group alias. Default is none.
        The final set of features generated by the predictor is set(features) - set(excludes).
    powers: Optional[List[int]]
        The list of powers to use when computing generalized weighted means of element properties.
        p=1 corresponds to the ordinary mean, p=2 is the root mean square, etc.

    """

    input_descriptor = _properties.Object(Descriptor, 'data.instance.input')
    features = _properties.List(_properties.String, 'data.instance.features')
    excludes = _properties.List(_properties.String, 'data.instance.excludes')
    powers = _properties.List(_properties.Integer, 'data.instance.powers')

    typ = _properties.String('data.instance.type', default='ChemicalFormulaFeaturizer',
                             deserializable=False)

    def __init__(self,
                 name: str,
                 *,
                 description: str,
                 input_descriptor: ChemicalFormulaDescriptor,
                 features: Optional[List[str]] = None,
                 excludes: Optional[List[str]] = None,
                 powers: Optional[List[int]] = None):
        self.name = name
        self.description = description
        self.input_descriptor = input_descriptor
        self.features = features if features is not None else ["standard"]
        self.excludes = excludes if excludes is not None else []
        self.powers = powers if powers is not None else [1]

    def __str__(self):
        return '<ChemicalFormulaFeaturizer {!r}>'.format(self.name)
