from uuid import uuid4

from citrine.informatics.data_sources import GemTableDataSource
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
                'type': 'Real',
                'descriptor_key': 'khs.sNH3 KierHallSmarts for {}'.format(col),
                'units': '',
                'lower_bound': 0,
                'upper_bound': 1000000000
            },
            {
                'type': 'Real',
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
        input_descriptor=MolecularStructureDescriptor(col),
        features=["all"],
        excludes=["standard"]
    )
    results = descriptors.from_predictor_responses(predictor=featurizer, inputs=[MolecularStructureDescriptor(col)])
    assert results == [
        RealDescriptor(
            key=r['descriptor_key'],
            lower_bound=r['lower_bound'],
            upper_bound=r['upper_bound'],
            units=r['units']
        ) for r in response_json['responses']
    ]
    assert session.last_call.path == '/projects/{}/material-descriptors/predictor-responses'\
        .format(descriptors.project_id)
    assert session.last_call.method == 'POST'


def test_descriptors_from_data_source():
    session = FakeSession()
    col = 'smiles'
    response_json = {
        'descriptors': [  # shortened sample response
            {
                'type': 'Real',
                'descriptor_key': 'khs.sNH3 KierHallSmarts for {}'.format(col),
                'units': '',
                'lower_bound': 0,
                'upper_bound': 1000000000
            },
            {
                'type': 'Real',
                'descriptor_key': 'khs.dsN KierHallSmarts for {}'.format(col),
                'units': '',
                'lower_bound': 0,
                'upper_bound': 1000000000
            },
        ]
    }
    session.set_response(response_json)
    descriptors = DescriptorMethods(uuid4(), session)
    data_source = GemTableDataSource(table_id='43357a66-3644-4959-8115-77b2630aca45', table_version=123)

    results = descriptors.descriptors_from_data_source(data_source=data_source)
    assert results == [
        RealDescriptor(
            key=r['descriptor_key'],
            lower_bound=r['lower_bound'],
            upper_bound=r['upper_bound'],
            units=r['units']
        ) for r in response_json['descriptors']
    ]
    assert session.last_call.path == '/projects/{}/material-descriptors/from-data-source'\
        .format(descriptors.project_id)
    assert session.last_call.method == 'POST'

