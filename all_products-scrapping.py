
import json
import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

CATEGORY_MAP = {
    "femme": "Femme",
    "homme": "Homme",
    "enfant": "enfant",
    "sac a dos": "Sac a dos",
    "football": "football",
    "randonnée": "randonnée",
}

def open_category_page(category_name):
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.decathlon.tn/")
    time.sleep(5)

    category_label = CATEGORY_MAP.get(category_name.lower())
    if not category_label:
        print(f"❌ Category '{category_name}' not found.")
        return None

    try:
        wrappers = driver.find_elements(By.CLASS_NAME, "main-categories__category-wrapper")
        for wrapper in wrappers:
            try:
                span = wrapper.find_element(By.CLASS_NAME, "main-caegories__title")
                if span.text.strip().lower() == category_label.lower():
                    wrapper.click()
                    print(f"✅ Navigated to '{category_label}' category.")
                    time.sleep(6)
                    return driver
            except:
                continue

        print(f"❌ Could not find category '{category_label}' on the homepage.")
        return None

    except Exception as e:
        print(f"⚠️ Error navigating to category: {e}")
        return None

def scrape_products_on_current_page(driver):
    product_cards = driver.find_elements(By.CSS_SELECTOR, "article.product-card")
    page_products = []

    for card in product_cards:
        soup = BeautifulSoup(card.get_attribute("outerHTML"), "html.parser")
        product_data = {
            "title": soup.select_one("a.js-product-card-link h2").text.strip() if soup.select_one("a.js-product-card-link h2") else "N/A",
            "brand": soup.select_one("header p").text.strip() if soup.select_one("header p") else "N/A",
            "price": soup.select_one("span.price_amount").text.strip() if soup.select_one("span.price_amount") else "N/A",
            "rating": soup.select_one("span.rating_label").text.strip() if soup.select_one("span.rating_label") else "N/A",
            "rating_count": soup.select_one("p.product-card_rating-count").text.strip() if soup.select_one("p.product-card_rating-count") else "N/A",
            "image_url": soup.select_one("img")["src"] if soup.select_one("img") else "N/A",
            "product_url": soup.select_one("a.js-product-card-link")["href"] if soup.select_one("a.js-product-card-link") else "N/A"
        }
        page_products.append(product_data)

    return page_products

def go_to_next_page(driver):
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
        if "disabled" in next_button.get_attribute("class"):
            return False
        else:
            next_page_url = next_button.get_attribute("href")
            driver.get(next_page_url)
            time.sleep(5)
            return True
    except:
        return False

def scrape_all_pages(driver):
    all_products = []
    page_number = 1

    while True:
        print(f"🔍 Scraping page {page_number}...")
        products = scrape_products_on_current_page(driver)
        all_products.extend(products)
        print(f"✅ Found {len(products)} products on page {page_number}.")

        if not go_to_next_page(driver):
            print("🚫 No more pages to scrape.")
            break

        page_number += 1

    print(f"\n📦 Total products scraped: {len(all_products)}")
    csv_filename = "all_products.csv"
    keys = ["title", "brand", "price", "rating", "rating_count", "image_url", "product_url"]
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_products)


    print(f"💾 All product data saved to '{csv_filename}'.")
# 🧪 Example usage
category = "femme"
driver = open_category_page(category)
if driver:
    scrape_all_pages(driver)
    input("Press Enter to close the browser...")
    driver.quit()