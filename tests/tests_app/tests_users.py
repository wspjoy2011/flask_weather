import unittest
from flask import url_for
from random import choice

from flask_login import login_user, logout_user

from app import create_app
from generate_data.db.create_test_database import create_db, USERS, PROFILES, ROLES
from app.auth.models import Role, User


class UsersTestCase(unittest.TestCase):
    """Test users"""

    @classmethod
    def setUpClass(cls):
        """Before all tests"""

    def setUp(self):
        """Before each test"""
        self.app = create_app('testing')
        self.db = self.app.config['db']
        self.users = USERS
        self.profiles = PROFILES
        self.roles = ROLES
        create_db(self.db, self.users, self.profiles, self.roles)
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """After each test"""
        self.ctx.pop()

    def test_show_users_page(self):
        """Test user data from show_user page"""
        response_first_page = self.client.get(url_for('main.show_emails'))
        response_second_page = self.client.get(url_for('main.show_emails', page=2))
        data = response_first_page.get_data(as_text=True) + response_second_page.get_data(as_text=True)
        code_first_page = response_first_page.status_code
        code_second_page = response_second_page.status_code
        self.assertEqual(code_first_page, 200)
        self.assertEqual(code_second_page, 200)
        for user in self.users:
            self.assertIn(f'<td>{user.full_name}</td>\n                '
                          f'<td>{user.email}</td>\n                '
                          f'<td>{user.role}</td>\n',
                          data)

    def test_edit_user_page(self):
        """Test edit user information"""
        admins = Role.select().where(Role.name == 'admin').first()
        users = User.select()
        random_admin = choice(admins.users)
        random_user = choice(users)

        login_user(random_admin)
        response = self.client.get(url_for('main.edit_email', user_id=random_user.id))
        data = response.get_data(as_text=True)
        code = response.status_code
        self.assertEqual(code, 200)
        self.assertIn(random_user.email, data)
        logout_user()

    def test_edit_page_with_anonymous_user(self):
        """Test to get edit page with anonymous user"""
        user_to_edit = choice(User.select())
        response = self.client.get(url_for('main.edit_email', user_id=user_to_edit.id), follow_redirects=True)
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('Please log in to access this page.', data)
        self.assertEqual(response.request.path, url_for('auth.login'))

    def test_edit_page_another_user_with_user_role(self):
        """Test edit another user information with user role, access denied"""
        users = Role.select().where(Role.name == 'user').first().users
        user_to_edit = choice(users)
        current_user = choice([user for user in users if user.id != user_to_edit.id])

        login_user(current_user)
        response = self.client.get(url_for('main.edit_email', user_id=user_to_edit.id), follow_redirects=True)
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn("You don&#39;t have access to edit this item.", data)
        logout_user()

    def test_edit_page_non_existent_user(self):
        """Test edit page with non-existing user id"""
        admin = choice(Role.select().where(Role.name == 'admin').first().users)
        fake_id = 777

        login_user(admin)
        response = self.client.get(url_for('main.edit_email', user_id=fake_id), follow_redirects=True)
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(f'User with id: {fake_id} not found.', data)
        logout_user()

    def test_update_username(self):
        """Test update user information"""
        self.app.config['WTF_CSRF_ENABLED'] = False
        admins = Role.select().where(Role.name == 'admin').first()
        users = User.select()
        random_admin = choice(admins.users)
        random_user = choice(users)

        login_user(random_admin)
        response = self.client.post(
            url_for('main.update_email', user_id=random_user.id),
            data={
                'id': random_user.id,
                'name': random_user.name + '_test',
                'email': random_user.email,
                'submit': 'Add'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn(f'{random_user.name}_test updated', data)
        logout_user()

    def test_update_user_with_existing_email(self):
        """Test update user information with existing email"""
        self.app.config['WTF_CSRF_ENABLED'] = False
        users = User.select()
        current_user = choice(users)
        test_user = choice([user for user in users if user.id != current_user.id])

        login_user(current_user)
        response = self.client.post(
            url_for('main.update_email', user_id=current_user.id),
            data={
                'id': current_user.id,
                'name': current_user.name,
                'email': test_user.email,
                'submit': 'Add'
            },
            follow_redirects=True
        )
        code = response.status_code
        data = response.get_data(as_text=True)
        self.assertEqual(code, 200)
        self.assertIn('Email already added into database', data)
        logout_user()


if __name__ == "__main__":
    unittest.main()
