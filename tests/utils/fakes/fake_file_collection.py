from citrine.resources.file_link import FileCollection, FileLink


class FakeFileCollection(FileCollection):

    def __init__(self):
        self.files = []

    def upload(self, file_path: str, dest_name: str = None) -> FileLink:
        self.files.append(file_path)
        return FileLink(url=file_path, filename=file_path)
