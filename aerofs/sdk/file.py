from .common import ContentState
from .interface import APIObject
from .interface import readonly
from .interface import synced


@readonly('id', sync=False)
@synced('name')
@synced('parent')
@readonly('last_modified')
@readonly('size')
@readonly('mime_type')
@readonly('path')
@synced('content')
@readonly('content_state')
@readonly('etag', sync=False)
class File(APIObject):
    def __init__(self, api, fid=None):
        super(File, self).__init__(api)

        self._id = fid
        self._name = None
        self._parent = None
        self._last_modified = None
        self._size = None
        self._mime_type = None
        self._path = None

        self._content = None
        self._content_state = None

        # TODO: here and elsewhere, update _etag usage ([None] doesn't work)
        self._etag = None

    def from_json(self, json):
        self._id = json['id']
        self._name = json['name']
        if 'parent' in json:  # not present in Children
            from .folder import Folder
            self._parent = Folder(self.api, json['parent'])
        self._last_modified = json.get('last_modified')  # not present on empty
                                                         # files
        self._size = json.get('size')  # not present on empty files
        self._mime_type = json['mime_type']

        # https://bitbucket.org/logilab/pylint/issues/729/enums-on-python-27-from-the-enum34-package
        # pylint: disable=E1136
        self._content_state = ContentState[json.get('content_state')]
        return self

    def load(self):
        data = self.api.get_file(self.id)
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def load_content(self):
        self._content = self.api.get_file_content(self.id)

        self._mime_type = self.api.response_headers['Content-Type']
        self._etag = self.api.response_headers['ETag']

    def load_path(self):
        data = self.api.get_folder_path(self.id)

        from .folder import Folder
        self._path = [Folder(self.api).from_json(f) for f in data['folders']]

    def save_content(self, matching=False):
        if not matching:
            self._etag = False

        self.api.upload_file_content(self.id, self._content,
                                     ifmatch=[self._etag])
        self.load()  # new metadata

    def save_name(self):
        self.move(self.parent.id, self.name, matching=True)

    def save_parent(self):
        self.move(self.parent.id, self.name, matching=True)

    def create(self, parent_id, name):
        data = self.api.create_file(parent_id, name)
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def move(self, parent_id, name, matching=False):
        if not matching:
            self._etag = None

        data = self.api.move_file(self.id, parent_id, name,
                                  ifmatch=[self._etag])
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def delete(self, matching=False):
        if not matching:
            self._etag = None

        self.api.delete_file(self.id, ifmatch=[self._etag])
