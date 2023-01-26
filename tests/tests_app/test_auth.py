import os
import re
import unittest
import io
from PIL import Image
from random import choice
from flask import url_for
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash
from peewee import fn

from app import create_app
from generate_data.db.create_test_database import USERS, PROFILES, ROLES
from app.weather.models import UserCity
from app.auth.models import User, Role, Profile
from app.auth.forms import RegisterForm


class UserTestCase(unittest.TestCase):
    profiles_data = None
    users_data = None
    app = None
    ctx = None
    db = None
    roles = None
    user_data = None
    user_profile = None
    admin_data = None
    admin_profile = None

    @classmethod
    def create_tables(cls):
        """Create tables and fill Roles for auth app"""
        cls.db.create_tables([User, Profile, Role, UserCity])

    @classmethod
    def create_roles(cls, roles):
        roles_instances = {}
        for role in roles:
            role_instance = Role(
                name=role
            )
            role_instance.save()
            roles_instances[role] = role_instance.id
        return roles_instances

    @classmethod
    def setUpClass(cls):
        """Before all tests"""
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False

        cls.db = cls.app.config['db']
        cls.users_data = USERS
        cls.profiles_data = PROFILES
        cls.create_tables()
        cls.roles = cls.create_roles(ROLES)
        cls.user_data = choice([user for user in cls.users_data if user.role == 'user'])
        cls.user_profile = choice(cls.profiles_data)
        cls.admin_data = choice([user for user in cls.users_data if user.role == 'admin'])
        cls.admin_profile = choice(cls.profiles_data)

        cls.ctx = cls.app.test_request_context()
        cls.ctx.push()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        """After each test"""
        cls.ctx.pop()

    def test_1_register_user(self):
        """Register user in auth register"""
        form = RegisterForm(
            username=self.user_data.full_name,
            email=self.user_data.email,
            info=self.user_profile.info,
            password=self.user_data.password,
            password_repeat=self.user_data.password,
            submit='Register'
        )
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': form.username.data,
                'email': form.email.data,
                'info': form.info.data,
                'password': form.password.data,
                'password_repeat': form.password.data,
                'submit': form.submit.data
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(
            f'{self.user_data.full_name} you can now login.',
            data
        )
        self.assertEqual(response.request.path, url_for('auth.login'))
        user = User.select().where(User.name == self.user_data.full_name).first()
        self.assertTrue(user)

    def test_2_register_admin(self):
        """Register admin in auth register"""
        form = RegisterForm(
            username=self.admin_data.full_name,
            email=self.admin_data.email,
            info=self.admin_profile.info,
            password=self.admin_data.password,
            password_repeat=self.admin_data.password,
            submit='Register'
        )
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': form.username.data,
                'email': form.email.data,
                'info': form.info.data,
                'password': form.password.data,
                'password_repeat': form.password.data,
                'submit': form.submit.data
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(
            f'{self.admin_data.full_name} you can now login.',
            data
        )
        self.assertEqual(response.request.path, url_for('auth.login'))
        admin = User.select().where(User.name == self.admin_data.full_name).first()
        self.assertTrue(admin)
        role_admin = Role.select().where(Role.name == 'admin').first()
        admin.role = role_admin
        admin.save()

    def test_aa_register_user_invalid_username(self):
        """Register user in auth register with invalid name"""
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': 'john_doe!',
                'email': 'some_email@gmail.com',
                'info': 'web developer',
                'password': 'asdfS@!345',
                'password_repeat': 'asdfS@!345',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(
            'Usernames must have only letters, numbers, dots or underscores',
            data
        )
        self.assertEqual(response.request.path, url_for('auth.register'))

    def test_ab_register_user_with_exist_username(self):
        """Register user in auth register with exist username"""
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': self.user_data.full_name,
                'email': 'some_email@gmail.com',
                'info': 'web developer',
                'password': 'asdfS@!345',
                'password_repeat': 'asdfS@!345',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('Username already in use.', data)
        self.assertEqual(response.request.path, url_for('auth.register'))

    def test_ac_register_user_with_exist_email(self):
        """Register user in auth register with exist username"""
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': 'john_doe_smith',
                'email': self.user_data.email,
                'info': 'web developer',
                'password': 'asdfS@!345',
                'password_repeat': 'asdfS@!345',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('Email already registered.', data)
        self.assertEqual(response.request.path, url_for('auth.register'))

    def test_ad_register_user_with_weak_password(self):
        """Register user in auth register with weak password"""
        response = self.client.post(
            url_for('auth.register'),
            data={
                'username': 'john_doe_smith',
                'email': 'some_email@gmail.com',
                'info': 'web developer',
                'password': 'asdfF345',
                'password_repeat': 'asdfS@!345',
                'submit': 'Register'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(
            'Password must be at least 8 chars include Upper, Lower, Digit, Punctuation',
            data
        )
        self.assertEqual(response.request.path, url_for('auth.register'))

    def test_ae_login_registered_user(self):
        """Login registered user"""
        response = self.client.post(
            url_for('auth.login'),
            data={
                'next': '',
                'email': self.user_data.email,
                'password': self.user_data.password,
                'remember_me': False,
                'submit': 'Log In'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(
            f'Welcome to the web application.\n    Hello,\n    \n    {self.user_data.full_name}!\n',
            data
        )
        self.assertEqual(response.request.path, url_for('main.index'))
        logout_user()

    def test_af_with_already_logged_user(self):
        user = User.select().where(User.email == self.user_data.email).first()
        login_user(user)
        response = self.client.post(
            url_for('auth.login'),
            data={
                'next': '',
                'email': self.user_data.email,
                'password': self.user_data.password,
                'remember_me': False,
                'submit': 'Log In'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('You are already logged in.', data)
        self.assertEqual(response.request.path, url_for('main.index'))
        logout_user()

    def test_ah_next_parameter_with_login_page(self):
        response = self.client.post(
            url_for('auth.login'),
            data={
                'next': url_for('auth.secret'),
                'email': self.user_data.email,
                'password': self.user_data.password,
                'remember_me': False,
                'submit': 'Log In'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn('Only authenticated users are allowed!', data)
        self.assertEqual(url, url_for('auth.secret'))
        logout_user()

    def test_ai_login_with_invalid_password(self):
        response = self.client.post(
            url_for('auth.login'),
            data={
                'next': '',
                'email': self.user_data.email,
                'password': self.admin_data.password,
                'remember_me': False,
                'submit': 'Log In'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn('Invalid username or password.', data)
        self.assertEqual(url, url_for('auth.login'))

    def test_aj_logout(self):
        user = User.select().where(User.email == self.user_data.email).first()
        login_user(user)
        response = self.client.get(
            url_for('auth.logout'),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn('You have been logged out.', data)
        self.assertEqual(url, url_for('main.index'))

        response_to_secret_page = self.client.get(
            url_for('auth.secret'),
            follow_redirects=True
        )
        code = response_to_secret_page.status_code
        data = response_to_secret_page.get_data(as_text=True)
        url = response_to_secret_page.request.path
        self.assertEqual(code, 200)
        self.assertIn('Please log in to access this page.', data)
        self.assertEqual(url, url_for('auth.login'))

    def test_ak_profile_page_of_current_user(self):
        user = User.select().where(User.email == self.user_data.email).first()
        login_user(user)
        response = self.client.get(
            url_for('auth.show_profile', user_id=user.id),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path

        self.assertEqual(code, 200)
        self.assertIn(f'Profile {user.name}', data)
        self.assertIn(user.email, data)
        self.assertIn(user.profile.info, data)
        self.assertIn(user.profile.avatar.split('&')[0], data)
        self.assertEqual(url, url_for('auth.show_profile', user_id=user.id))
        logout_user()

    def test_al_profile_page_with_no_exist_profile_id(self):
        user = User.select().where(User.email == self.user_data.email).first()
        max_user_id = User.select(fn.MAX(User.id)).scalar()
        login_user(user)
        response = self.client.get(
            url_for('auth.show_profile', user_id=max_user_id + 1),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(url, url_for('auth.show_profile', user_id=max_user_id + 1))
        self.assertIn(
            '404 Not Found: The requested URL was not found on the server. '
            'If you entered the URL manually please check your spelling and try again.',
            data
        )
        self.assertEqual(code, 404)
        logout_user()

    def test_am_get_profile_of_another_user(self):
        current_user = User.select().where(User.email == self.user_data.email).first()
        another_user_data = choice(
            [user_data for user_data in self.users_data
             if user_data.email != current_user.email and user_data.role != 'admin']
        )

        another_user_profile_data = choice(self.profiles_data)
        another_user_profile = Profile(
            info=another_user_profile_data.info,
            avatar=another_user_profile_data.avatar)
        another_user_profile.save()
        another_user = User(
            name=another_user_data.full_name,
            email=another_user_data.email,
            password_hash=generate_password_hash(another_user_data.password),
            role=Role.select().where(Role.name == 'user').first(),
            profile=another_user_profile
        )
        another_user.save()

        login_user(current_user)
        response = self.client.get(
            url_for('auth.show_profile', user_id=another_user.id),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path

        self.assertEqual(code, 200)
        self.assertIn('You don&#39;t have access to this page', data)
        self.assertEqual(url, url_for('main.index'))
        logout_user()

    def test_an_get_profile_of_another_user_with_admin_role(self):
        admin = User.select().where(User.email == self.admin_data.email).first()
        user = User.select().where(User.email == self.user_data.email).first()

        login_user(admin)
        response = self.client.get(
            url_for('auth.show_profile', user_id=user.id),
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path

        self.assertEqual(code, 200)
        self.assertIn(f'Profile {user.name}', data)
        self.assertEqual(url, url_for('auth.show_profile', user_id=user.id))

        logout_user()

    def test_ao_change_avatar_of_user(self):
        user = User.select().where(User.email == self.user_data.email).first()
        image_name = 'test.png'
        image = Image.new('RGB', (60, 30), color='red')
        image.save(image_name, format='png')

        login_user(user)
        with open(image_name, 'rb') as image_file:
            file_data = {'avatar': (image_file, image_name)}
            response = self.client.post(
                url_for('auth.upload_avatar', user_id=user.id),
                data=file_data,
                follow_redirects=True,
                content_type='multipart/form-data'
            )

        files = os.listdir(os.getcwd())
        for file in files:
            if file.endswith(".png"):
                os.remove(os.path.join(os.getcwd(), file))

        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertTrue(re.search(rf'[0-9]+\.[0-9]+_{image_name}\suploaded', data))
        self.assertEqual(url, url_for('auth.show_profile', user_id=user.id))
        logout_user()

    def test_ap_change_avatar_of_user_with_incorrect_file(self):
        user = User.select().where(User.email == self.user_data.email).first()
        image_name = 'test.jpg'
        login_user(user)
        file_data = {'avatar': (io.BytesIO(b'test_image_content'), image_name)}
        response = self.client.post(
            url_for('auth.upload_avatar', user_id=user.id),
            data=file_data,
            follow_redirects=True,
            content_type='multipart/form-data'
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn(f'{image_name} is not allowed image type', data)
        self.assertEqual(url, url_for('auth.show_profile', user_id=user.id))

        logout_user()

    def test_ar_change_avatar_of_user_with_empty_filename(self):
        user = User.select().where(User.email == self.user_data.email).first()
        login_user(user)
        response = self.client.post(
            url_for('auth.upload_avatar', user_id=user.id),
            data={'avatar': (io.BytesIO(b'test_image_content'), '')},
            follow_redirects=True,
            content_type='multipart/form-data'
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn('Nothing to upload', data)
        self.assertEqual(url, url_for('auth.show_profile', user_id=user.id))
        logout_user()

    def test_as_change_avatar_of_another_user_with_admin_role(self):
        admin = User.select().where(User.email == self.admin_data.email).first()
        another_user = User.select().where(User.email == self.user_data.email).first()
        login_user(admin)
        response = self.client.post(
            url_for('auth.upload_avatar', user_id=another_user.id),
            data={'avatar': (io.BytesIO(b'test_image_content'), 'test.jpg')},
            follow_redirects=True,
            content_type='multipart/form-data'
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        url = response.request.path
        self.assertEqual(code, 200)
        self.assertIn('You cannot change avatar of another user', data)
        self.assertEqual(url, url_for('main.index'))
        logout_user()

    def test_at_get_password_from_user(self):
        user = User.select().where(User.email == self.user_data.email).first()
        with self.assertRaises(AttributeError) as error:
            password = user.password
        self.assertEqual('password is not a readable attribute', str(error.exception))
