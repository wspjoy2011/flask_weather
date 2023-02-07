import datetime
import bleach
from peewee import TextField
from markdown import markdown

from app import User
from app.base_model import BaseModel, DateTimeField, ForeignKeyField, CharField


class Post(BaseModel):
    body = TextField()
    image = CharField(null=True)
    timestamp = DateTimeField(default=datetime.datetime.now)
    author = ForeignKeyField(User, backref='posts')

    @property
    def body_html(self):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        html = bleach.linkify(bleach.clean(
            markdown(str(self.body), output_format='html'),
            tags=allowed_tags, strip=True))
        return html

