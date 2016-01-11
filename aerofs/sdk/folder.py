from .interface import APIObject
from .interface import readonly
from .interface import synced


@readonly('files', sync=False)
@readonly('folders', sync=False)
class Children(APIObject):
    def __init__(self, api):
        super(Children, self).__init__(api)

        self._files = None
        self._folders = None

    load = lambda x: None

    def from_json(self, json):
        from .file import File
        self._files = frozenset([File(self.api).from_json(f)
                                 for f in json['files']])
        self._folders = frozenset([Folder(self.api).from_json(f)
                                   for f in json['folders']])
        return self


@readonly('id', sync=False)
@synced('name')
@synced('parent')
@readonly('is_shared')
@readonly('shared_folder')
@readonly('path')
@readonly('children')
@readonly('etag', sync=False)
class Folder(APIObject):
    def __init__(self, api, fid=None):
        super(Folder, self).__init__(api)

        self._id = fid
        self._name = None
        self._parent = None
        self._is_shared = None
        self._shared_folder = None
        self._path = None
        self._children = None

        self._etag = None

    def from_json(self, json):
        self._id = json['id']
        self._name = json['name']
        if 'parent' in json:  # not present in Path / Children
            self._parent = Folder(self.api, json['parent'])
        self._is_shared = json['is_shared']
        if self._is_shared:
            from .shared_folder import SharedFolder
            self._shared_folder = SharedFolder(self.api, json['sid'])
        return self

    def load(self):
        data = self.api.get_folder(self.id)
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def load_children(self):
        data = self.api.get_folder_children(self.id)
        self._children = Children(self.api).from_json(data)

    def load_path(self):
        data = self.api.get_folder_path(self.id)
        self._path = tuple([Folder(self.api).from_json(f)
                            for f in data['folders']])

    def save_name(self):
        self.move(self.parent.id, self.name, matching=True)

    def save_parent(self):
        self.move(self.parent.id, self.name, matching=True)

    def create(self, parent_id, name):
        data = self.api.create_folder(parent_id, name)
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def move(self, parent_id, name, matching=False):
        if not matching:
            self._etag = None

        data = self.api.move_folder(self.id, parent_id, name,
                                    ifmatch=[self._etag])
        self.from_json(data)

        self._etag = self.api.response_headers['ETag']

    def share(self):
        self.api.share_folder(self.id)
        self.load()

    def delete(self, matching=False):
        if not matching:
            self._etag = None

        self.api.delete_folder(self.id, ifmatch=[self._etag])
