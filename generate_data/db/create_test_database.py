import json
from typing import List, Dict

from app.auth.models import User, Profile, Role
from app.weather.models import UserCity
from generate_data.main import main as generate_users_profiles
from generate_data.data.user_data import ROLES
from generate_data.tools.generate_users import UsersDTO


def clear_db():
    """Delete data from User, Profile, Role tables"""
    UserCity().delete().execute()
    User.delete().execute()
    Role.delete().execute()
    Profile.delete().execute()


def write_roles_to_db(roles):
    """Write roles to db"""
    roles_indexes = {}
    for role in roles:
        role_instance = Role(
            name=role
        )
        role_instance.save()
        roles_indexes[role] = role_instance.id
    return roles_indexes


def write_profile_to_db(profile):
    """Write profile to db"""
    profile_instance = Profile(
        avatar=profile.avatar,
        info=profile.info
    )
    profile_instance.save()
    return profile_instance.id


def write_user_to_db(user, profile_id, role_id):
    """Write profile to db"""
    user_instance = User(
        name=user.full_name,
        email=user.email,
        password=user.password,
        role=role_id,
        profile=profile_id
    )
    user_instance.save()


def prepare_user_credentials(users: UsersDTO):
    """Prepare users credentials into json"""
    users_prepared_to_json = []
    for user in users:
        temp = {
            'nickname': user.full_name,
            'email': user.email,
            'password': user.password,
            'role': user.role
        }
        users_prepared_to_json.append(temp)
    return users_prepared_to_json


def write_users_credentials_to_json(users: List[Dict[str, str]], json_file: str = 'credentials.json'):
    """Write user credential to json  file"""
    with open(json_file, 'w') as file:
        json.dump(users, file, indent=4)


def create_db(db, users, profiles, roles, delete=False):
    """Fill database with test data"""
    if delete:
        clear_db()

    db.create_tables([User, Profile, Role])
    roles = write_roles_to_db(roles)

    if delete:
        users_prepared_to_json = prepare_user_credentials(users)
        write_users_credentials_to_json(users_prepared_to_json)

    for user, profile in zip(users, profiles):
        profile_id = write_profile_to_db(profile)
        role_id = roles[user.role]
        write_user_to_db(user, profile_id, role_id)


USERS, PROFILES = generate_users_profiles()
