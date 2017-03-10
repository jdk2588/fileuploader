from documents.con import dbcon

from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, BooleanField

class UploadedFiles(Document):
    token = StringField()
    filename = StringField()
    cloudfilename = StringField()
    contenttype = StringField()
    created_on = DateTimeField()
    modified_on = DateTimeField()
    is_uploaded = BooleanField(default=False)

    meta = {
        'collection': 'uploadedfiles',
    }

    def get_object(self):
        _fields = ("token", "filename", "contenttype")
        ret = {}

        for _e in _fields:
            ret[_e] = self[_e]


        return ret

    def save(self, *args, **kwargs):

        now = datetime.utcnow()
        self.modified_on = now
        if not self.created_on:
            self.created_on = now

        super(UploadedFiles, self).save(*args, **kwargs)
