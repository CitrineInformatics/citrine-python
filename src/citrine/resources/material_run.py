"""Resources that represent material run data objects."""
import json
import os
from typing import List, Dict, Optional, Type, Iterator

from citrine._rest.resource import Resource
from citrine._serialization.properties import List as PropertyList
from citrine._serialization.properties import Optional as PropertyOptional
from citrine._serialization.properties import String, LinkOrElse, Mapping, Object
from citrine._utils.functions import set_default_uid
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.material_spec import MaterialSpecCollection
from citrine.resources.object_runs import ObjectRun, ObjectRunCollection
from taurus.entity.file_link import FileLink
from taurus.entity.link_by_uid import LinkByUID
from taurus.entity.object.material_run import MaterialRun as TaurusMaterialRun
from taurus.entity.object.material_spec import MaterialSpec as TaurusMaterialSpec
from taurus.entity.object.process_run import ProcessRun as TaurusProcessRun
from taurus.json import TaurusEncoder
from taurus.util import writable_sort_order


class MaterialRun(ObjectRun, Resource['MaterialRun'], TaurusMaterialRun):
    """
    A material run.

    Parameters
    ----------
    name: str
        Name of the material run.
    uids: Map[str, str], optional
        A collection of
        `unique IDs <https://citrineinformatics.github.io/taurus-documentation/
        specification/unique-identifiers/>`_.
    tags: List[str], optional
        `Tags <https://citrineinformatics.github.io/taurus-documentation/specification/tags/>`_
        are hierarchical strings that store information about an entity. They can be used
        for filtering and discoverability.
    notes: str, optional
        Long-form notes about the material run.
    process: ProcessRun
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


class MaterialRunCollection(ObjectRunCollection[MaterialRun]):
    """Represents the collection of all material runs associated with a dataset."""

    _path_template = 'projects/{project_id}/datasets/{dataset_id}/material-runs'
    _dataset_agnostic_path_template = 'projects/{project_id}/material-runs'
    _individual_key = 'material_run'
    _collection_key = 'material_runs'

    @classmethod
    def get_type(cls) -> Type[MaterialRun]:
        """Return the resource type in the collection."""
        return MaterialRun

    def get_history(self, scope, id) -> Type[MaterialRun]:
        """
        Get the history associated with a material.

        The history contains every single every process, ingredient and material that went into
        the root material as well as the measurements that were performed on all of those
        materials. The returned object is a material run with all of its fields fully populated.

        Parameters
        ----------
        scope: str
            The scope used to locate the material.
        id: str
            The unique id corresponding to `scope`. The lookup will be most efficient if you use
            the Citrine ID (scope='id') of the material.

        Returns
        -------
        MaterialRun
            A material run that has all of its fields fully populated with the processes,
            ingredients, measurements, and other materials that were involved in the history
            of the object.

        """
        base_path = os.path.dirname(self._get_path(ignore_dataset=True))
        path = base_path + "/material-history/{}/{}".format(scope, id)
        data = self.session.get_resource(path)

        # Add the root to the context and sort by writable order
        blob = dict()
        blob["context"] = sorted(
            data['context'] + [data['root']],
            key=lambda x: writable_sort_order(x["type"])
        )
        root_uid_scope, root_uid_id = next(iter(data['root']['uids'].items()))
        # Add a link to the root as the "object"
        blob["object"] = LinkByUID(scope=root_uid_scope, id=root_uid_id)

        # Serialize using normal json (with the TaurusEncoder) and then deserialize with the
        # TaurusJson encoder in order to rebuild the material history
        return MaterialRun.get_json_support().loads(
            json.dumps(blob, cls=TaurusEncoder, sort_keys=True))

    def filter_by_spec(self,
                       spec_id: str,
                       spec_scope: str = 'id',
                       per_page: int = 20) -> Iterator[MaterialRun]:
        """
        [ALPHA] Get all material runs associated with a material spec.

        The material spec is specified by its scope and id.

        :param spec_id: The unique id corresponding to `scope`.
            The lookup will be most efficient if you use the Citrine ID (scope='id')
            of the material spec.
        :param spec_scope: The scope used to locate the material spec.
        :param per_page: The number of results to return per page.
        :return: A search result of material runs
        """
        path_prefix = MaterialSpecCollection(self.project_id,
                                             self.dataset_id,
                                             self.session)._get_path(ignore_dataset=True)
        path = path_prefix + "/" + spec_scope + "/" + spec_id + "/material-runs"
        raw_objects = self.session.cursor_paged_resource(self.session.get_resource,
                                                         path,
                                                         per_page=per_page,
                                                         version="v1")
        return (self.build(raw) for raw in raw_objects)

    # Retrieve all material runs associated with a material template
    def filter_by_template(self,
                           template_id: str,
                           template_scope: str = 'id',
                           per_page: int = 20) -> Iterator[MaterialRun]:
        """
        [ALPHA] Get all material runs associated with a material template.

        The material template is specified by its scope and id.

        :param template_id: The unique id corresponding to `scope`.
            The lookup will be most efficient if you use the Citrine ID (scope='id')
            of the material template.
        :param template_scope: The scope used to locate the material template.
        :param per_page: The number of results to return per page.
            Also used for intermediate queries.
        :return: A search result of material runs
        """
        spec_collection = MaterialSpecCollection(self.project_id, self.dataset_id, self.session)
        specs = spec_collection.filter_by_template(template_id,
                                                   template_scope=template_scope,
                                                   per_page=per_page)
        return (run for runs in (self.filter_by_spec(spec.uids['id'],
                                 per_page=per_page)for spec in specs)
                for run in runs)
