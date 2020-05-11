from typing import List
from uuid import UUID

from citrine._session import Session
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor


# Not a full Collection since CRUD operations are not valid for Descriptors
class DescriptorMethods:
    """[ALPHA] A set of methods returning descriptors which require connection to the backend."""

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def from_predictor_responses(self, predictor: Predictor,
                                 inputs: List[Descriptor]) -> List[Descriptor]:
        """
        [ALPHA] Get responses for a predictor, given an input space.

        Parameters
        ----------
        predictor : Predictor
            The predictor whose available responses are to be computed.
        inputs : List[Descriptor]
            The input space to the predictor.

        Returns
        -------
        List[Descriptor]
            The computable responses of the predictor given the provided input space (as
            descriptors).

        """
        response = self.session.post_resource(
            path='/projects/{}/material-descriptors/predictor-responses'.format(self.project_id),
            json={
                'predictor': predictor.dump()['config'],
                'inputs': [i.dump() for i in inputs]
            }
        )
        return [Descriptor.build(r) for r in response['responses']]
