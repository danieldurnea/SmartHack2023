import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

def scrape(nume):
    # Specify the path to your webdriver executable. You may need to download the appropriate driver for your browser.
    # Create a new instance of the Chrome driver (you can use other drivers like Firefox, Edge, etc.)
    service = ChromeService(executable_path=ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options, service=service)

    # Open the listafirme.ro search page
    driver.get(url="https://www.listafirme.ro/search.asp")

    # Perform any further interactions with the page as needed

    search_name = driver.find_element(By.NAME, 'searchfor')

    print(search_name)

    search_name.send_keys(nume)


    button_xpath = driver.find_element(By.XPATH, '//button[text()="Caută"]')
    button_xpath.click()

    button_row = driver.find_element(By.CLASS_NAME, 'clickable-row')
    button_row.click()

    time.sleep(2)

    all_handles = driver.window_handles

    new_tab_handle = all_handles[-1]
    driver.switch_to.window(new_tab_handle)

    CUI = driver.find_element(By.CSS_SELECTOR, 'tbody tr:nth-child(3) > :nth-child(2)')
    temp = CUI.text
    driver.quit()
    return temp

# Close the browser window when done
# driver.quit()

print(scrape("Regina Maria"))
