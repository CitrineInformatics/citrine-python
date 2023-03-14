import pytest

from citrine.informatics.descriptors import FormulationDescriptor
from citrine.informatics.constraints import ScalarRangeConstraint, AcceptableCategoriesConstraint, \
    IngredientCountConstraint, IngredientFractionConstraint, LabelFractionConstraint
from citrine.informatics.design_spaces import ProductDesignSpace, EnumeratedDesignSpace, FormulationDesignSpace
from citrine.informatics.objectives import ScalarMaxObjective, ScalarMinObjective
from citrine.informatics.scores import LIScore, EIScore, EVScore

informatics_string_data = [
    (IngredientCountConstraint(
        formulation_descriptor=FormulationDescriptor.hierarchical(),
        min=0, max=1
    ), "<IngredientCountConstraint 'x'>"),
    (IngredientFractionConstraint(
        formulation_descriptor=FormulationDescriptor.hierarchical(),
        ingredient='y',
        min=0,
        max=1
    ),"<IngredientFractionConstraint 'x'::'y'>"),
    (LabelFractionConstraint(
        formulation_descriptor=FormulationDescriptor.hierarchical(),
        label='y',
        min=0,
        max=1
    ), "<LabelFractionConstraint 'x'::'y'>"),
    (ScalarRangeConstraint(descriptor_key='z'), "<ScalarRangeConstraint 'z'>"),
    (AcceptableCategoriesConstraint(descriptor_key='x', acceptable_categories=[]), "<AcceptableCategoriesConstraint 'x'>"),
    (ProductDesignSpace(name='my design space', description='does some things'),
     "<ProductDesignSpace 'my design space'>"),
    (EnumeratedDesignSpace('enumerated', description='desc', descriptors=[], data=[]), "<EnumeratedDesignSpace 'enumerated'>"),
    (FormulationDesignSpace(
        name='formulation',
        description='desc',
        formulation_descriptor=FormulationDescriptor.hierarchical(),
        ingredients={'y'},
        constraints=set(),
        labels={}
    ), "<FormulationDesignSpace 'formulation'>"),
    (ScalarMaxObjective('z'), "<ScalarMaxObjective 'z'>"),
    (ScalarMinObjective('z'), "<ScalarMinObjective 'z'>"),
    (LIScore(objectives=[], baselines=[]), "<LIScore>"),
    (EIScore(objectives=[], baselines=[], constraints=[]), "<EIScore>"),
    (EVScore(objectives=[], constraints=[]), "<EVScore>"),
]


@pytest.mark.parametrize('obj,repr', informatics_string_data)
def test_str_representation(obj, repr):
    assert str(obj) == repr
