import undetected_chromedriver as uc


def get_undetected_chromedriver():
    PROXY = 'socks5://localhost:9050'

    options = uc.ChromeOptions()
    options.add_argument(f'--proxy-server={PROXY}')

    driver = uc.Chrome(options=options)
    return driver
