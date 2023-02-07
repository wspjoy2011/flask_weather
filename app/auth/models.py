import datetime
import itertools
from peewee import CharField, ForeignKeyField, TextField, DateTimeField
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.base_model import BaseModel


class Role(BaseModel):
    name = CharField(max_length=100, unique=True, index=True)


class Profile(BaseModel):
    avatar = CharField()
    info = TextField(null=True)


class User(BaseModel, UserMixin):
    name = CharField(max_length=100)
    email = CharField(max_length=150, unique=True, index=True)
    password_hash = CharField(max_length=128)
    last_visit = DateTimeField(default=datetime.datetime.now)
    role = ForeignKeyField(Role, backref='users')
    profile = ForeignKeyField(Profile)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_following(self, user):
        followed = (
            Follow
            .select()
            .where(
                (Follow.follower_id == self.id) & (Follow.followed_id == user.id)
            ).first()
        )
        return bool(followed)

    def follow(self, user):
        if not self.is_following(user):
            follow_user = Follow(follower_id=self, followed_id=user)
            follow_user.save()

    def unfollow(self, user):
        if self.is_following(user):
            (Follow
                .delete()
                .where(
                    (Follow.follower_id == self.id) & (Follow.followed_id == user.id))
            ).execute()

    @property
    def followed_posts(self):
        followed = Follow.select().where(Follow.follower_id == self.id)
        followed_users_posts = [user.followed_id.posts for user in followed]
        followed_users_posts = list(itertools.chain.from_iterable(followed_users_posts))
        return sorted(followed_users_posts, key=lambda post: post.timestamp, reverse=True)


class Follow(BaseModel):
    follower_id = ForeignKeyField(User, backref='follower', on_delete='CASCADE')
    followed_id = ForeignKeyField(User, backref='followed', on_delete='CASCADE')
    timestamp = DateTimeField(default=datetime.datetime.now)
