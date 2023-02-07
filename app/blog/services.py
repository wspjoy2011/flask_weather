from app.auth.models import Follow


def get_followers(user):
    followers = Follow.select().where(Follow.followed_id == user.id)
    follows = [{'user': item.follower_id, 'timestamp': item.timestamp}
               for item in followers]
    return follows


def get_followed(user):
    followed = Follow.select().where(Follow.follower_id == user.id)
    follows = [{'user': item.followed_id, 'timestamp': item.timestamp}
               for item in followed]
    return follows


def get_followers_count(user):
    return Follow.select().where(Follow.followed_id == user.id).count()


def get_followed_count(user):
    return Follow.select().where(Follow.follower_id == user.id).count()
