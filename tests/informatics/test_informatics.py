import pytest

from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.constraints import ScalarRangeConstraint, CategoricalConstraint,\
    IngredientCountConstraint, IngredientFractionConstraint, LabelFractionConstraint
from citrine.informatics.design_spaces import ProductDesignSpace, EnumeratedDesignSpace, FormulationDesignSpace
from citrine.informatics.objectives import ScalarMaxObjective, ScalarMinObjective
from citrine.informatics.processors import GridProcessor, EnumeratedProcessor
from citrine.informatics.scores import LIScore, EIScore
from citrine.informatics.reports import ModelSummary, FeatureImportanceReport


informatics_string_data = [
    (IngredientCountConstraint(FormulationDescriptor('x'), 0, 1), "<IngredientCountConstraint 'x'>"),
    (IngredientFractionConstraint(FormulationDescriptor('x'), 'y', 0, 1), "<IngredientFractionConstraint 'x'::'y'>"),
    (LabelFractionConstraint(FormulationDescriptor('x'), 'y', 0, 1), "<LabelFractionConstraint 'x'::'y'>"),
    (ScalarRangeConstraint('z'), "<ScalarRangeConstraint 'z'>"),
    (CategoricalConstraint('x', []), "<CategoricalConstraint 'x'>"),
    (ProductDesignSpace('my design space', 'does some things', []), "<ProductDesignSpace 'my design space'>"),
    (EnumeratedDesignSpace('enumerated', 'desc', [], []), "<EnumeratedDesignSpace 'enumerated'>"),
    (FormulationDesignSpace('formulation', 'desc', FormulationDescriptor('x'), {'y'}, set(), {}),
     "<FormulationDesignSpace 'formulation'>"),
    (ScalarMaxObjective('z', 1.0, 10.0), "<ScalarMaxObjective 'z'>"),
    (ScalarMinObjective('z', 1.0, 10.0), "<ScalarMinObjective 'z'>"),
    (GridProcessor('my thing', 'does a thing', dict(x=1)), "<GridProcessor 'my thing'>"),
    (EnumeratedProcessor('my enumerated thing', 'enumerates', 10), "<EnumeratedProcessor 'my enumerated thing'>"),
    (LIScore("LI(z)", "score for z", [], []), "<LIScore 'LI(z)'>"),
    (EIScore("EI(x)", "score for x", [], [], []), "<EIScore 'EI(x)'>"),
    (FeatureImportanceReport("reflectivity", {}), "<FeatureImportanceReport 'reflectivity'>"),
    (ModelSummary("my model", "ML Model", [], [], {}, [], "predictor name"), "<ModelSummary 'my model'>"),
]


@pytest.mark.parametrize('obj,repr', informatics_string_data)
def test_str_representation(obj, repr):
    assert str(obj) == repr
