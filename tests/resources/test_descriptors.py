from uuid import uuid4

from citrine.informatics.descriptors import MolecularStructureDescriptor, RealDescriptor
from citrine.informatics.predictors import MolecularStructureFeaturizer
from citrine.resources.descriptors import DescriptorMethods
from tests.utils.session import FakeSession


def test_from_predictor_responses():
    session = FakeSession()
    col = 'smiles'
    response_json = {
        'responses': [  # shortened sample response
            {
                'category': 'Real',
                'descriptor_key': 'khs.sNH3 KierHallSmarts for {}'.format(col),
                'units': '',
                'lower_bound': 0,
                'upper_bound': 1000000000
            },
            {
                'category': 'Real',
                'descriptor_key': 'khs.dsN KierHallSmarts for {}'.format(col),
                'units': '',
                'lower_bound': 0,
                'upper_bound': 1000000000
            },
        ]
    }
    session.set_response(response_json)
    descriptors = DescriptorMethods(uuid4(), session)
    featurizer = MolecularStructureFeaturizer(
        name="Molecule featurizer",
        description="description",
        descriptor=MolecularStructureDescriptor(col),
        features=["all"],
        excludes=["standard"]
    )
    results = descriptors.from_predictor_responses(featurizer, [MolecularStructureDescriptor(col)])
    assert results == [
        RealDescriptor(
            key=r['descriptor_key'],
            lower_bound=r['lower_bound'],
            upper_bound=r['upper_bound'],
        ) for r in response_json['responses']
    ]
    assert session.last_call.path == '/projects/{}/material-descriptors/predictor-responses'\
        .format(descriptors.project_id)
    assert session.last_call.method == 'POST'
