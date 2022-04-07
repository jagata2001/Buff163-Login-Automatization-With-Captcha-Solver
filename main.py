from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

from captcha_solver_class import Captcha_solver
from time import sleep
class Buff163_login:
    def __init__(self,phone_number,password,country_sign='GE'):
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(executable_path="./chromedriver",options=options)
        self.driver.maximize_window()
        self.country_sign = country_sign
        self.phone_number = phone_number
        self.password = password
        self.url = "https://buff.163.com/"

    def load(self):
        self.driver.get(self.url)
        wait = WebDriverWait(self.driver, 20)
        nav = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'nav.nav_entries')))
        login = nav.find_element_by_tag_name("li")
        login.click()
        login_frame = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'login-frame')))
        self.iframe = login_frame.find_element_by_tag_name("iframe")
        #switch to login iframe
        self.driver.switch_to.frame(self.iframe)

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, f'tab0'))).click()

    def login(self,max_captcha_try=10):
        wait = WebDriverWait(self.driver, 20)
        self.driver.find_element_by_id("mobile-itl-div").click()
        country_phone_prexfixs = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'j-country.u-country')))
        ge_prefix = country_phone_prexfixs.find_element_by_class_name(f"flag-{self.country_sign}")
        ge_prefix.click()
        self.driver.find_element_by_id("phoneipt").send_keys(self.phone_number)
        self.driver.find_element_by_xpath("//div[@class='u-input box']/input[2]").send_keys(self.password)

        old_image_for_move = ''
        old_background_img = ''
        captcha = False
        for _ in range(max_captcha_try):
            slider = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='yidun_slider']")))

            image_for_move = wait.until(EC.presence_of_element_located((By.XPATH, f"//img[@class='yidun_jigsaw' and @src!='{old_image_for_move}']"))).get_attribute("src")
            background_img = wait.until(EC.presence_of_element_located((By.XPATH, f"//img[@class='yidun_bg-img' and @src!='{old_background_img}']"))).get_attribute("src")
            old_image_for_move = image_for_move
            old_background_img = background_img
            captcha_solver = Captcha_solver(
                image_for_move,
                background_img
            )
            resp = False
            for _ in range(3):
                resp = captcha_solver.load_images()
                if resp:
                    break

            if resp:
                #perform captcha solve
                x_move = captcha_solver.solve_capthca()
                #means that captcha is not solved
                if x_move == False:
                    continue
                #convert 320 px returned data for image with 300px width
                x_move = x_move - ((x_move*((20*100)/320))/100)
                if x_move <=100:
                    x_move+=5
                elif x_move<=200:
                    x_move+=8
                elif x_move<=260:
                    x_move+=5

                actionchain = ActionChains(self.driver)
                actionchain.click_and_hold(slider)
                actionchain.pause(1)
                actionchain.move_by_offset(x_move,0)
                actionchain.pause(1)
                actionchain.click()
                actionchain.perform()

                try:
                    wait_for_captcha_result = WebDriverWait(self.driver, 5)
                    wait_for_captcha_result.until(EC.presence_of_element_located((By.CLASS_NAME, 'yidun.yidun--light.yidun--float.yidun--jigsaw.yidun--success')))
                    captcha = True
                    break
                except:
                    #captcha solve false
                    pass
                #to verify after failed in captcha solve
                try:
                    for_verify_failed = WebDriverWait(self.driver, 3)
                    for_verify_failed.until(EC.presence_of_element_located((By.CLASS_NAME, 'yidun_control.yidun_control--moving'))).click()
                except:
                    pass
        if captcha:
            self.driver.switch_to.default_content()
            #remember me
            self.driver.find_element_by_xpath("//div[@id='remember-me']/span/i").click()
            #keep me signed in for 10 days
            self.driver.find_element_by_xpath("//div[@id='agree-checkbox']/span/i").click()

            #switch to login iframe
            self.driver.switch_to.frame(self.iframe)

            #login
            wait.until(EC.element_to_be_clickable((By.ID, 'submitBtn'))).click()


            wait_for_login_check = WebDriverWait(self.driver, 30)
            try:
                wait_for_login_check.until(EC.presence_of_element_located((By.XPATH, "//p/a[@class='f_12px' and text()='Log out']")))
            except:
                return {"status":False,"message":f"Login failed for user: {self.username}. The probable problem may be incorrect username or password"}

            return {"status":True, "message":"successfully logged in","cookies":self.driver.get_cookies()}
        else:
            return {"status":False, "message":f"Failed to solve captcha maximum try count exceeded {max_captcha_try}"}

    def close(self):
        if self.driver != None:
            self.driver.quit()

if __name__ == "__main__":
    buff = Buff163_login("username","passwd")#,'GE'
    print("first page laoding...")
    buff.load()
    print("trying to login...")
    status = buff.login()
    print(status)
    buff.close()


#https://buff.163.com/api/market/goods?game=csgo&page_size=80&page_num=
