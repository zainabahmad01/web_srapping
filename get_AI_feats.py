import json
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import winsound
import signal
import sys

chrome_options = Options()
chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--silent")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=chrome_options)
loca = ["Toronto"]
wait = WebDriverWait(driver, 10)

restaurants = []
scraped_urls = set()

def save_json():
    with open('restaurants_Ai_feats.json', 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=4)

def handle_captcha():
    try:
        captcha_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'captcha')]")
        ))
        if captcha_element:
            print("CAPTCHA detected. Please solve it manually.")
            winsound.Beep(528, 2500)
            WebDriverWait(driver, 300).until_not(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'captcha')]")
            ))
            print("CAPTCHA solved. Resuming the script...")
    except Exception:
        print("No CAPTCHA detected. Continuing script execution.")

def scrape_restaurant_details(card_url):
    driver.get(card_url+"#allmeals")
    time.sleep(random.randint(3, 4))
    handle_captcha()
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    restaurant_data = {}
    
    try:
        restaurant_data['name'] = soup.find('h1', class_='notranslate').get_text(strip=True)
    except AttributeError:
        restaurant_data['name'] = None
    try:
        restaurant_data['phone_number'] = soup.find('a', class_='call').get_text(strip=True)
    except AttributeError:
        restaurant_data['phone_number'] = None
    
    features = []
    feature_elements = soup.select(".groupdiv a.tag")
    
    for feature in feature_elements:
        feature_name = feature.find('span').get_text(strip=True)
        feature_class = " ".join(feature.get("class", [])).replace("tag", "").strip()
        features.append({"name": feature_name, "class": feature_class})
    
    restaurant_data['features'] = features
    return restaurant_data

def scroll_random_distance():
    scroll_distance = random.randint(300, 500)
    driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
    time.sleep(2)

def signal_handler(sig, frame):
    print('Terminating and saving data...')
    save_json()
    driver.quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

for location in loca:
    driver.get(f"https://restaurantguru.com/restaurant-{location}-t1")
    time.sleep(random.uniform(3, 4))
    
    try:
        restaurant_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "restaurant_row")))
        while len(restaurants) <= 1000:
            for index in range(len(restaurant_cards)):
                try:
                    restaurant_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "restaurant_row")))
                    card = restaurant_cards[index]
                    
                    card_link_element = card.find_element(By.CSS_SELECTOR, 'a.title_url')
                    card_link = card_link_element.get_attribute('href')
                    
                    if card_link not in scraped_urls:
                        restaurant_details = scrape_restaurant_details(card_link)
                        restaurants.append(restaurant_details)
                        scraped_urls.add(card_link)
                        
                        if len(restaurants) % 20 == 0:
                            print(f"Scraped {len(restaurants)} restaurants.")
                        
                        if len(restaurants) >= 1000:
                            break
                        
                        driver.back()
                        time.sleep(random.uniform(3, 4))
                        scroll_random_distance()
                except Exception as e:
                    print(f"Error processing card: {e}")
    except Exception as e:
        print(f"Error fetching restaurant cards: {e}")

save_json()
driver.quit()