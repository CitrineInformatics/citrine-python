# This contains factories for creating test input, using factory boy
# https://factoryboy.readthedocs.io/en/latest/index.html

# Naming convention here is to use "*DataFactory" for dictionaries used as API input/out, and
# <ModelName>Factory for the domain objects themselves

from random import randrange

import factory
from citrine.informatics.scores import LIScore
from citrine.resources.dataset import Dataset
from citrine.resources.file_link import _Uploader
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.process_template import ProcessTemplate
from gemd.entity.link_by_uid import LinkByUID


class ProjectDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    status = 'CREATED'
    created_at = None


class UserDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    screen_name = factory.Faker('name')
    position = factory.Faker('job')
    email = factory.Faker('email')
    is_admin = factory.Faker('boolean')


class GemTableDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    version = randrange(10)
    signed_download_url = factory.Faker('uri')


class ListGemTableVersionsDataFactory(factory.DictFactory):
    tables = [GemTableDataFactory()]


class TableConfigJSONDataFactory(factory.DictFactory):
    """ This is simply the JSON Blob stored in an Table Config Version"""
    name = factory.Faker("company")
    description = factory.Faker('bs')
    rows = []
    columns = []
    variables = []
    datasets = []

class TableConfigVersionJSONDataFactory(factory.DictFactory):
    ara_definition = factory.SubFactory(TableConfigJSONDataFactory)
    id = factory.Faker('uuid4')
    version_number = randrange(10)

class WithIdDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')

class TableConfigResponseDataFactory(factory.DictFactory):
    """This is the TableConfig object that encapsulates both version and definition info from the server"""

    definition = factory.SubFactory(WithIdDataFactory)
    version = factory.SubFactory(TableConfigVersionJSONDataFactory)

class DatasetDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')
    deleted = False
    created_by = factory.Faker('uuid4')
    updated_by = factory.Faker('uuid4')
    deleted_by = factory.Faker('uuid4')
    create_time = None
    update_time = None
    delete_time = None
    public = False


class IDDataFactory(factory.DictFactory):
    id = factory.Faker('uuid4')


class LinkByUIDInputFactory(factory.DictFactory):
    id = factory.Faker('uuid4')
    type = 'link_by_uid'
    scope = 'id'


class FileLinkDataFactory(factory.DictFactory):
    url = factory.Faker('uri')
    filename = factory.Faker('file_name')
    type = 'file_link'


class MaterialRunDataFactory(factory.DictFactory):
    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = ["color"]
    notes = None
    process = factory.SubFactory(LinkByUIDInputFactory)
    sample_type = 'experimental'
    spec = None
    file_links = []
    type = 'material_run'


class LinkByUIDFactory(factory.Factory):
    class Meta:
        model = LinkByUID

    scope = 'id'
    id = factory.Faker('uuid4')


class MaterialRunFactory(factory.Factory):
    class Meta:
        model = MaterialRun

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    notes = None
    process = factory.SubFactory(LinkByUIDFactory)
    sample_type = 'experimental'
    spec = None
    file_links = []


class DatasetFactory(factory.Factory):
    class Meta:
        model = Dataset

    name = factory.Faker('company')
    summary = factory.Faker('catch_phrase')
    description = factory.Faker('bs')


class _UploaderFactory(factory.Factory):
    class Meta:
        model = _Uploader

    @factory.post_generation
    def assign_values(obj, create, extracted):
        obj.bucket = 'citrine-datasvc'
        obj.object_key = '334455'
        obj.upload_id = 'dea3a-555'
        obj.region_name = 'us-west'
        obj.aws_access_key_id = 'dkfjiejkcm'
        obj.aws_secret_access_key = 'ifeemkdsfjeijie8759235u2wjr388'
        obj.aws_session_token = 'fafjeijfi87834j87woa'
        obj.s3_version = '2'


class MLIScoreFactory(factory.Factory):
    class Meta:
        model = LIScore

    name = factory.Faker('bs')
    description = factory.Faker('catch_phrase')
    baselines = []
    objectives = []
    constraints = []


class MaterialSpecFactory(factory.Factory):
    class Meta:
        model = MaterialSpec

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    notes = None
    process = factory.SubFactory(LinkByUIDFactory)
    file_links = []
    template = None
    properties = []


class MaterialTemplateFactory(factory.Factory):
    class Meta:
        model = MaterialTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    properties = []
    description = factory.Faker('catch_phrase')


class MaterialSpecDataFactory(factory.DictFactory):
    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = ["color"]
    notes = None
    process = factory.SubFactory(LinkByUIDInputFactory)
    template = None
    file_links = []
    type = 'material_spec'


class ProcessTemplateFactory(factory.Factory):
    class Meta:
        model = ProcessTemplate

    uids = factory.SubFactory(IDDataFactory)
    name = factory.Faker('color_name')
    tags = []
    description = factory.Faker('catch_phrase')
    conditions = []
    parameters = []
