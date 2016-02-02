from PIL import Image
import deathbycaptcha


class CachedProperty(object):
    def __init__(self, function, name=None, doc=None):
        self.function = function
        self.__name__ = name or self.function.__name__
        self.__doc__ = doc or self.function.__doc__
        self.__module__ = self.function.__module__

    def __get__(self, *args):
        if args[0] is None:
            return None
        else:
            value = self.function(args[0])
            args[0].__dict__[self.function.__name__] = value
            return value


def get_element_screenshot(driver, element, filename):
    bounding_box = (
        element.location['x'],
        element.location['y'],
        (element.location['x'] + element.size['width']),
        (element.location['y'] + element.size['height'])
    )
    return bounding_box_screenshot(driver, bounding_box, filename)


def bounding_box_screenshot(driver, bounding_box, filename):
    driver.save_screenshot(filename)
    base_image = Image.open(filename)
    cropped_image = base_image.crop(bounding_box)
    base_image = base_image.resize(cropped_image.size)
    base_image.paste(cropped_image, (0, 0))
    base_image.save(filename)
    return base_image


def captcha_decoder(client, filename):
    try:
        balance = client.get_balance()

        captcha = client.decode(filename, 30)
        if captcha:
            print("CAPTCHA %s solved: %s" % (captcha["captcha"], captcha["text"]))
            return captcha

    except deathbycaptcha.AccessDeniedException:
        return False


def solve_captcha(driver):
    img = driver.find_elements_by_xpath("//*[contains(@id, 'wlspispHIPBimg')]")[0]
    if not get_element_screenshot(driver, img, 'captcha.png'):
        return False

    text = driver.find_elements_by_xpath("//*[contains(@id, 'wlspispSolutionElement')]")[0]
    text.clear()

    captcha = captcha_decoder('captcha.png')
    for ch in captcha['text']:
        text.send_keys(ch)
    return captcha
