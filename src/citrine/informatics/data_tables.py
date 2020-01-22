from citrine._serialization import properties
from citrine._serialization.serializable import Serializable


class DataTable(Serializable['DataTable']):
    table_id = properties.UUID('table_id')
    table_version = properties.String('table_version')

    def __init__(self, table_id: str):
        self.table_id = table_id
        self.table_version = 'latest'   # This will be writable once the API does something with it
