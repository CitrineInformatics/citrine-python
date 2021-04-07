from typing import List, Optional

from citrine._rest.resource import Resource
from citrine.informatics.descriptors import ChemicalFormulaDescriptor
from citrine.informatics.predictors import Predictor

__all__ = ['ChemicalFormulaFeaturizer']


class ChemicalFormulaFeaturizer(Resource['ChemicalFormulaFeaturizer'], Predictor):
    """
    A featurizer for chemical formulae. Inspired by Magpie.

    The ChemicalFormulaFeaturizer computes a configurable set of features on chemical formula data.
    The features are functions of element-level properties, which are inspired by
    `Magpie <https://bitbucket.org/wolverton/magpie/src/master/>`_. The features are configured
    using the ``features`` and ``excludes`` arguments, which accept either feature names or predefined
    aliases. Many features are element-wise weighted means of element-level properties. How to
    compute the mean is configured using the ``powers`` argument.

    The default is the "standard" alias, corresponding to features that are intuitive and
    often correlate with properties of interest. Other aliases are "physical," "electronic,"
    and "periodicTable."

    The following features are element-wise means of elemental properties.

    - "Pauling electronegativity"
    - "Number of d valence electrons"
    - "Number of unfilled f valence electrons"
    - "Number of f valence electrons"
    - "Number of unfilled p valence electrons"
    - "Number of p valence electrons"
    - "Number of unfilled s valence electrons"
    - "Number of s valence electrons"
    - "Total number of unfilled valence electrons"
    - "Total number of valence electrons"
    - "Elemental work function"
    - "Elemental polarizability"
    - "Radius of d orbitals"
    - 

    Parameters
    ----------

    """

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptor: ChemicalFormulaDescriptor,
                 features: List[str] = None,
                 excludes: List[str] = None,
                 powers: List[int] = None):
        self.name = name
        self.description = description
        self.input_descriptor = input_descriptor
        self.features = features if features is not None else ["standard"]
        self.excludes = excludes if excludes is not None else []
        self.powers = powers if powers is not None else [2]

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ChemicalFormulaFeaturizer {!r}>'.format(self.name)
