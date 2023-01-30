from selenium import webdriver
from selenium.webdriver.common.by import By


browser = webdriver.Chrome()
browser.get("http://localhost:5000")
print(browser.title)
register_link = browser.find_element(By.ID, 'registerLink')
register_link.click()

browser.find_element(By.ID, 'username').send_keys('test_user_selenium')
browser.find_element(By.ID, 'email').send_keys('test_user_selenium@gmail.com')
browser.find_element(By.ID, 'info').send_keys('Python web developer')
browser.find_element(By.ID, 'password').send_keys('Wspjoy2011!')
browser.find_element(By.ID, 'password_repeat').send_keys('Wspjoy2011!')
browser.find_element(By.ID, 'submit').click()
print(browser.page_source)
browser.close()
browser.quit()
