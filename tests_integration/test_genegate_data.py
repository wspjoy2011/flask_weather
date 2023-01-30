import json
import random
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Dict

from definitions import PATH_TO_CREDENTIALS


class TestGenerateDB(unittest.TestCase):
    browser: webdriver.Chrome = None
    base_url: str = None
    random_user: Dict[str, str] = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.browser = webdriver.Chrome()
        cls.base_url = "http://localhost:5000/"

    def test_aa_generate_database(self):
        self.browser.get(self.base_url)
        self.assertEqual(self.browser.title, 'Home page')
        register_link = self.browser.find_element(By.ID, 'submit')
        register_link.click()
        alert_text = self.browser.find_element(By.ID, 'alert_block').text
        self.assertIn('Database filled with test data', alert_text)

    def test_ab_login_with_new_generated_data(self):
        with open(PATH_TO_CREDENTIALS) as file:
            credentials = json.load(file)
        type(self).random_user = random.choice(credentials)

        login_link = self.browser.find_element(By.ID, 'loginLink')
        login_link.click()
        self.assertEqual(self.browser.title, 'Login page')
        self.browser.find_element(By.ID, 'email').send_keys(self.random_user['email'])
        self.browser.find_element(By.ID, 'password').send_keys(self.random_user['password'])
        self.browser.find_element(By.ID, 'submit').click()
        hello_message = self.browser.find_element(By.TAG_NAME, 'h1').text
        self.assertIn(f'Welcome to the web application. Hello, {self.random_user["nickname"]}!', hello_message)
        self.assertEqual(self.browser.current_url, self.base_url)

    def test_ac_show_city_weather_and_add_to_monitoring(self):
        city = 'Tokyo'
        country = 'Japan'

        self.browser.find_element(By.LINK_TEXT, 'Weather').click()
        self.browser.find_element(By.LINK_TEXT, 'Search city').click()

        self.assertEqual(self.browser.title, 'Get city weather')
        self.assertEqual(self.browser.current_url, self.base_url + 'weather/')

        self.browser.find_element(By.ID, 'city_name').send_keys(city)
        self.browser.find_element(By.ID, 'submit').click()

        city_header = self.browser.find_element(By.TAG_NAME, 'h3').text
        self.assertIn(f'Weather info about city {city}, {country}', city_header)

        self.browser.find_element(By.ID, 'addCity').click()
        alert_text = self.browser.find_element(By.ID, 'alert_block').text
        self.assertIn(f'City: Tokyo added to list of user {self.random_user["nickname"]}', alert_text)
        time.sleep(5)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.browser.quit()
