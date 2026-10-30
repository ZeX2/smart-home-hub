import os
import atexit
import threading
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .unlock_gate_data import PORTAL_LOGIN_URL, GATES
from .secrets import USR, PWD

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

class UnlockGateApi():

    def __init__(self):
        # One browser for all gates, so unlocks must take turns
        self.lock = threading.Lock()
        # Chrome takes seconds to start, so start it in the background; unlock_door waits for it
        self.driver_thread = threading.Thread(target=self.start_driver)
        self.driver_thread.start()

    def start_driver(self):
        # atexit doesn't run when the app is killed or loses power, so clear out Chrome left over from earlier runs
        for pattern in ['enable-automation', 'chromedriver']:
            subprocess.run(['pkill', '-f', pattern])
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        try:
            try:
                self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            except Exception as e:
                self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            self.driver = webdriver.Chrome(service=ChromeService(executable_path='/usr/lib/chromium-browser/chromedriver'), options=options)
        # Else chromedriver and Chrome keep running after the app exits
        atexit.register(self.driver.quit)

    def get_gates(self):
        return list(GATES.keys())

    def unlock_door(self, gate_name):
        self.driver_thread.join()
        with self.lock:
            gate_id = GATES[gate_name]

            self.driver.get(PORTAL_LOGIN_URL)

            self.driver.find_element(By.ID, 'user_login').send_keys(USR)
            self.driver.find_element(By.ID, 'user_pass').send_keys(PWD)

            login_btn_element = self.driver.find_elements(By.CLASS_NAME, 'btn.btn-primary')[0]
            self.driver.execute_script('arguments[0].click();', login_btn_element)

            def booking_href_ready(driver):
                links = driver.find_elements(By.XPATH, "//a[@class='btn btn-primary' and text()='Öppna']")
                if not links:
                    return False
                href = links[0].get_attribute('href') or ''
                return href if 'RemoteLogin' in href else False

            booking_href = WebDriverWait(self.driver, 20).until(booking_href_ready)
            self.driver.get(booking_href)

            door_element_id = f'entranceDoor_{gate_id}'
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, door_element_id)))

            self.driver.execute_script(f'UnlockEntranceDoor({gate_id})')

            def door_unlocked(driver):
                return driver.find_element(By.ID, door_element_id).get_attribute('data-status') == 'unlocked'

            try:
                return WebDriverWait(self.driver, 15).until(door_unlocked)
            except TimeoutException:
                return False

if __name__ == "__main__":
    ug = UnlockGateApi()
    print(ug.unlock_door(ug.get_gates()[0]))
