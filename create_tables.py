# from peewee import SqliteDatabase
#
# from app.base_model import database_proxy
# from app.auth.models import User, Profile
#
#
# db = SqliteDatabase('user.db')
# database_proxy.initialize(db)
# db.create_tables([Profile, User])


# import hashlib
#
# email = "someone111@somewhere.com"
# size = 80
#
# digest = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
# url = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
#             digest, size)
