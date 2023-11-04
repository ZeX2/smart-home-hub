import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from .unlock_gate_data import PORTAL_LOGIN_URL, GATES
from .secrets import USR, PWD

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

class UnlockGateApi():

    def __init__(self):
        options = Options()
        options.add_argument("--headless=new")
        try:
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        except:
            self.driver = webdriver.Chrome(service=ChromeService(executable_path='/usr/lib/chromium-browser/chromedriver'), options=options)

    def get_gates(self):
        return list(GATES.keys())

    def unlock_door(self, gate_name):
        gate_id = GATES[gate_name]

        self.driver.get(PORTAL_LOGIN_URL)

        self.driver.find_element(By.ID, 'user_login').send_keys(USR)
        self.driver.find_element(By.ID, 'user_pass').send_keys(PWD)

        login_btn_element = self.driver.find_elements(By.CLASS_NAME, 'btn.btn-primary')[0]
        login_btn_element.click()
        time.sleep(0.25)
        booking_btn_element = self.driver.find_elements(By.CLASS_NAME, 'btn.btn-primary')[10]
        self.driver.get(booking_btn_element.get_attribute('href'))

        door_element_id = f'entranceDoor_{gate_id}'
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, door_element_id)))
        door_element = self.driver.find_element(By.ID, door_element_id)

        self.driver.execute_script(f'AjaxUnlockEntranceDoor({gate_id})')
        time.sleep(2)
        door_element = self.driver.find_element(By.ID, door_element_id)

        return door_element.get_attribute('data-status') == 'unlocked'

if __name__ == "__main__":
    ug = UnlockGateApi()
    print(ug.unlock_door(ug.get_gates()[0]))
