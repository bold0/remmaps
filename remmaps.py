from selenium import webdriver


from config import *
from util import *

fp = open('pwd.csv', 'r')
data = fp.readlines()
fp.close()


def get_credential():
    return random.choice(data).strip().split('\t')


class Remmaps:
    def __init__(self, username, password):
        self._server = None
        self.username = username
        self.password = password
        self.base_url = "https://mail.live.com"
        self.captcha_filename = 'captcha.png'
        self.default_timeout = 30

        self.captcha_decoder_client = deathbycaptcha.SocketClient(DEATHBYCAPTCHA_LOGIN, DEATHBYCAPTCHA_PASSWORD)

    @CachedProperty
    def driver(self):
        profile = webdriver.FirefoxProfile(FIREFOX_PROFILE)
        profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        return webdriver.Firefox(profile)

    def get_element_by_xpath(self, string_search, ignore_errors=True, retries=3, timeout=1):
        count = 0
        self.driver.implicitly_wait(timeout)
        while count < retries:
            count += 1
            try:
                ret = self.driver.find_elements_by_xpath(string_search)
                if not ret:
                    time.sleep(timeout)
                    continue
                self.driver.implicitly_wait(30)
                return ret
            except Exception as e:
                time.sleep(timeout)
                if ignore_errors:
                    if count < retries:
                        continue
                    self.driver.implicitly_wait(30)
                    return False
                else:
                    self.driver.implicitly_wait(30)
                    raise e

    def avoid_captcha(self):
        need_captcha = self.get_element_by_xpath("//*[contains(@id, 'wlspispHIPBimg')]")
        if not need_captcha:
            return True

        get_element_screenshot(self.driver, need_captcha[0], self.captcha_filename)
        solved_captcha = captcha_decoder(self.captcha_decoder_client, self.captcha_filename)
        if not solved_captcha:
            raise ValueError("Can't solve captcha!")

        _captcha_input = self.get_element_by_xpath("//*[contains(@id, 'wlspispSolutionElement')]")
        if _captcha_input:
            _captcha_input[0].clear()
            _captcha_input[0].send_keys(solved_captcha['text'])

            _submit = self.get_element_by_xpath("//*[contains(@type, 'submit')]")
            if _submit:
                _submit[0].click()

                _captcha_error = self.get_element_by_xpath("//*[contains(@id, 'wlspispHIPErrorWrong')]", retries=3)
                if _captcha_error:
                    self.captcha_decoder_client.report(solved_captcha['captcha'])
                else:
                    return True

            else:
                raise ValueError("Can't decode captcha!")

    def login(self):
        login_input = self.driver.find_elements_by_xpath("//*[contains(@type, 'email')]")
        password_input = self.driver.find_elements_by_xpath("//*[contains(@type, 'password')]")
        submit_button = self.driver.find_elements_by_xpath("//*[contains(@type, 'submit')]")
        if not login_input or not password_input or not submit_button:
            raise ValueError('Email, password or submit element not found.')

        login_input[0].clear()
        login_input[0].send_keys(self.username)

        password_input[0].clear()
        password_input[0].send_keys(self.password)

        submit_button[0].click()

        invalid_login = self.get_element_by_xpath("//*[contains(@id, 'idTd_Tile_ErrorMsg_Login')]", retries=1, timeout=0.1)
        if invalid_login:
            raise ValueError('Invalid login!')

        self.avoid_captcha()


    def spam(self, recipient, subject=''):
        self.driver.get('https://mail.live.com/?page=Compose')

        to_field = self.get_element_by_xpath("//textarea[@class='cp_primaryInput cp_anyInput t_urtc']")
        if not to_field:
            raise ValueError('"To" field not found.')

        for _to_field in to_field:
            if 'email' in _to_field.get_attribute('aria-label').lower():
                _to_field.click()
                _to_field.send_keys(recipient)
                break


        options = self.driver.find_elements_by_class_name('c_mlu')
        for opt in options:
            if opt.text.startswith('Op'):
                opt.click()
                sub = self.driver.find_elements_by_xpath('.//span[@class = "Caption"]')
                if sub:
                    for _sub in sub:
                        if 'html' in _sub.text.lower():
                            _sub.click()
                            break
        _subject = self.get_element_by_xpath("//*[contains(@id, 'watermarkedInputControl')]")
        if not _subject:
            raise ValueError('"Subject" field not found.')

        _subject[0].send_keys(subject)

        #parei aqui, nao consigo pegar o field de input da mensagem
        self.driver.find_element_by_xpath("//body[@onclick='clk(event);']").click()
        self.driver.find_element_by_xpath("//a[@id='SendMessage']/span[2]").click()

    def outlook(self):
        self.driver.implicitly_wait(30)
        self.driver.get(self.base_url + '/')
        self.login()
        recipients = ['email1@blabla.com',
                      'email2@hotmail.com']
        for r in recipients:
            self.spam(r, 'assunto')


if __name__ == '__main__':
    while True:
        acc = get_credential()
        acc = ['login@hotmail.com', 'password']
        c = Remmaps(acc[0], acc[1])

        c.outlook()
