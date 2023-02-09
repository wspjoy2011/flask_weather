import datetime
import bleach
from peewee import TextField
from markdown import markdown

from app import User
from app.base_model import BaseModel, DateTimeField, ForeignKeyField, CharField, BooleanField


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


class Comment(BaseModel):
    body = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    disabled = BooleanField()
    author = ForeignKeyField(User, backref='comments', on_delete='CASCADE')
    post = ForeignKeyField(Post, backref='comments', on_delete='CASCADE')

    @property
    def body_html(self):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        html = bleach.linkify(bleach.clean(
            markdown(str(self.body), output_format='html'),
            tags=allowed_tags, strip=True))
        return html
