"""Resources that represent material run data objects."""
from typing import List, Dict, Optional, Type
import os
import json

from citrine._utils.functions import set_default_uid
from citrine._rest.resource import Resource
from citrine._session import Session
from citrine.resources.data_concepts import DataConcepts, DataConceptsCollection
from citrine._serialization.properties import String, LinkOrElse, Mapping, Object
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from taurus.client.json_encoder import TaurusEncoder
from taurus.entity.dict_serializable import DictSerializable
from taurus.entity.file_link import FileLink
from taurus.entity.link_by_uid import LinkByUID
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.entity.object.material_run import MaterialRun as TaurusMaterialRun
from taurus.entity.object.material_spec import MaterialSpec as TaurusMaterialSpec
from taurus.client.json_encoder import loads


class MaterialRun(DataConcepts, Resource['MaterialRun'], TaurusMaterialRun):
    """
    A material run.

    Parameters
    ----------
    name: str
        Name of the material run.
    uids: Map[str, str], optional
        A collection of unique identifiers, each a key-value pair. The key is the "scope"
        and the value is the identifier. The scope "id" is reserved for the internal Citrine ID,
        which will always be a uuid4.
    tags: List[str], optional
        A set of tags. Tags can be used for filtering.
    notes: str, optional
        Long-form notes about the material run.
    process: ProcessSpec
        Process that produces this material.
    sample_type: str, optional
        The form of this sample. Optionals are "experimental", "virtual", "production", or
        "unknown." Default is "unknown."
    spec: MaterialSpec
        The material specification of which this is an instance.
    file_links: List[FileLink], optional
        Links to associated files, with resource paths into the files API.

    Attributes
    ----------
    measurements: List[MeasurementRun], optional
        Measurements performed on this material. The link is established by creating the
        measurement run and settings its `material` field to this material run.

    """

    _response_key = TaurusMaterialRun.typ  # 'material_run'

    name = String('name')
    uids = Mapping(String('scope'), String('id'), 'uids')
    tags = PropertyOptional(PropertyList(String()), 'tags')
    notes = PropertyOptional(String(), 'notes')
    process = PropertyOptional(LinkOrElse(), 'process')
    sample_type = String('sample_type')
    spec = PropertyOptional(LinkOrElse(), 'spec')
    file_links = PropertyOptional(PropertyList(Object(FileLink)), 'file_links')
    typ = String('type')

    def __init__(self,
                 name: str,
                 uids: Optional[Dict[str, str]] = None,
                 tags: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 process: Optional[TaurusProcessRun] = None,
                 sample_type: Optional[str] = "unknown",
                 spec: Optional[TaurusMaterialSpec] = None,
                 file_links: Optional[List[FileLink]] = None):
        DataConcepts.__init__(self, TaurusMaterialRun.typ)
        TaurusMaterialRun.__init__(self, name=name, uids=set_default_uid(uids),
                                   tags=tags, process=process,
                                   sample_type=sample_type, spec=spec,
                                   file_links=file_links, notes=notes)

    def __str__(self):
        return '<Material run {!r}>'.format(self.name)

    @classmethod
    def _build_soft_linked_objects(cls, obj, obj_with_soft_links, session: Session = None):
        """
        Build the MeasurementRun objects that this MaterialRun has soft links to.

        The measurement runs are found in `obj_with_soft_link`

        This method modifies the object in place.

        Parameters
        ----------
        obj: MaterialRun
            A MaterialRun object that might be missing some links to MeasurementRun objects.
        obj_with_soft_links: dict or \
        :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            A representation of the MaterialRun in which the MeasurementRuns are encoded.
            We consider both the possibility that this is a dictionary with a 'measurements' key
            and that it is a
            :py:class:`DictSerializable <taurus.entity.dict_serializable.DictSerializable>`
            (presumably a
            :py:class:`TaurusMeasurementRun <taurus.entity.measurement_run.MeasurementRun>`)
            with a .measurements field.
        session: Session, optional
            Citrine session used to connect to the database.

        Returns
        -------
        None
            The MaterialRun object is modified so that it has links to its MeasurementRuns.

        """
        measurements = None
        # Get the measurements list, if it exists.
        if isinstance(obj_with_soft_links, dict):
            if obj_with_soft_links.get('measurements'):
                measurements = obj_with_soft_links['measurements']
        if isinstance(obj_with_soft_links, DictSerializable):
            if hasattr(obj_with_soft_links, 'measurements'):
                measurements = getattr(obj_with_soft_links, 'measurements')
        if measurements is None:
            return

        from citrine.resources.measurement_run import MeasurementRun
        for meas in measurements:
            # Cycle through measurements and if they are not LinkByUID, build them and then
            # set their `material` field to obj
            assert isinstance(meas, DictSerializable)
            if isinstance(meas, LinkByUID):
                pass
            setattr(meas, 'material', None)
            meas_object = MeasurementRun.build(meas, session)
            setattr(meas_object, 'material', obj)
        return


class MaterialRunCollection(DataConceptsCollection[MaterialRun]):
    """Represents the collection of all material runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-runs'
    _individual_key = 'material_run'
    _collection_key = 'material_runs'

    @classmethod
    def get_type(cls) -> Type[MaterialRun]:
        """Return the resource type in the collection."""
        return MaterialRun

    def get_history(self, scope, id):
        """Get the history associated with a material."""
        base_path = os.path.dirname(self._get_path(ignore_dataset=True))
        path = base_path + "/material-history/{}/{}".format(scope, id)
        data = self.session.get_resource(path)
        # Rehydrate a taurus object based on the data
        model = loads(json.dumps([data['context'], data['root']], cls=TaurusEncoder))
        # Convert taurus objects into citrine-python objects
        return MaterialRun.build(model)
