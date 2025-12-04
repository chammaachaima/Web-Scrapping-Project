from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import csv

product_urls = [
    "https://www.decathlon.tn/p/9713-71642-chaussure-course-a-pied-homme-run-one-bleu.html",
    "https://www.decathlon.tn/p/325971-81443-chaussures-de-running-homme-jogflow-5001-blanc-bleu-rouge.html",
    "https://www.decathlon.tn/p/9713-71632-chaussure-course-a-pied-homme-run-one-gris.html",
    "https://www.decathlon.tn/p/337693-109698-chaussures-de-running-homme-jogflow-1001-noir-gris.html",
    "https://www.decathlon.tn/p/325939-55595-chaussures-de-running-femme-jogflow-5001-noir.html",
    "https://www.decathlon.tn/p/325939-54219-chaussures-de-running-femme-jogflow-5001-gris-fonce-et-rose.html",
    "https://www.decathlon.tn/p/145853-57669-chaussures-de-running-femme-kalenji-run-active-noir-rose.html",
    "https://www.decathlon.tn/p/325939-54226-chaussures-de-running-femme-jogflow-5001-orange.html",
    "https://www.decathlon.tn/p/308317-34349-tente-de-camping-mh100-3-places.html",
    "https://www.decathlon.tn/p/342646-79254-fauteuil-inclinable-confortable-pliant-de-camping.html",
    "https://www.decathlon.tn/p/13259-23371-matelas-mousse-de-trekking-mt100-180-x-50-cm-1-personne.html",    
    "https://www.decathlon.tn/p/326697-57496-lampe-torche-a-piles-100-lumens-tl100.html",
    "https://www.decathlon.tn/p/130208-20116-table-de-camping-pliante-4-tabourets-4-a-6-personnes-bleu.html",
    "https://www.decathlon.tn/p/338993-55069-sac-de-couchage-pour-le-camping-arpenaz-10.html",
    "http://decathlon.tn/p/313089-24501-cabine-de-douche-pour-le-camping-2seconds.html"

]


def extract_product_name_from_url(url):
    try:
        path = urlparse(url).path  
        slug = path.split('/')[-1]  
        name_part = slug.replace('.html', '').split('-', 2)[-1]  # remove numeric ID and ".html"
        name_part = name_part.replace('-', ' ')
        return name_part.title()  # Capitalize nicely
    except:
        return "Decathlon Product"

def generate_review_key(review_dict):
    key_parts = [
        review_dict.get('Title', '').lower().strip()[:50],
        review_dict.get('Content', '').lower().strip()[:100],
        review_dict.get('Date', '').strip(),
    ]
    return '|'.join(key_parts)

def scrape_decathlon_reviews(url, max_reviews=3000):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    chrome_options.add_argument("--lang=fr")

    print("Initializing WebDriver...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    reviews_data = []
    seen_review_keys = set()

    try:
        driver.set_window_size(1920, 1080)
        print(f"Navigating to {url}...")
        driver.get(url)
        print("Waiting for page to load...")
        time.sleep(5)

        try:
            reviews_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.oyreviews-content-item"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", reviews_section)
            time.sleep(2)
        except TimeoutException:
            print("Could not find reviews section")
            return [], "Unknown Product"

        current_page = 1
        max_pages = 13

        while current_page <= max_pages:
            print(f"\n Processing page {current_page}...")

            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.oyreviews-content-item"))
            )

            review_elements = driver.find_elements(By.CSS_SELECTOR, "div.oyreviews-content-item")
            print(f"Found {len(review_elements)} review elements")

            page_new_reviews = 0
            for review_elem in review_elements:
                try:
                    def safe_extract(selector, default='N/A'):
                        try:
                            elem = review_elem.find_element(By.CSS_SELECTOR, selector)
                            return elem.text.strip()
                        except NoSuchElementException:
                            return default
                    try:
                        rating_elem = review_elem.find_element(By.CSS_SELECTOR, "ul.star-rating")
                        rating = rating_elem.get_attribute("title").strip()
                    except NoSuchElementException:
                        rating = 'N/A'

                    review_dict = {
                        'Rating':  rating,
                        'Date': safe_extract("time.dtreviewed", 'N/A'),
                        'Title': safe_extract("span.fn.review-title", 'N/A'),
                        'Content': safe_extract("blockquote.description", 'N/A'),
                        'Reviewer': safe_extract("div.reviewer", 'N/A').split('|')[0].strip(),
                        'Verified': 'Yes' if 'Vérifié' in safe_extract("div.reviewer", '') else 'No',
                        'Brand Response': safe_extract("blockquote.response", 'No response')
                    }

                    review_key = generate_review_key(review_dict)

                    if review_key not in seen_review_keys:
                        reviews_data.append(review_dict)
                        seen_review_keys.add(review_key)
                        page_new_reviews += 1
                        print(f"Review #{len(reviews_data)}: {review_dict['Title'][:40]}...")
                    else:
                        print(f" Skipping potential duplicate: {review_dict['Title'][:40]}...")

                except Exception as e:
                    print(f"Error processing review: {e}")

            print(f"Added {page_new_reviews} new reviews on page {current_page}")

            if len(reviews_data) >= max_reviews:
                print("Reached max review count")
                break

            try:
                next_buttons = driver.find_elements(By.XPATH, "//button[@title='next page']")
                if not next_buttons:
                    print("No more next page buttons found")
                    break

                next_button = next_buttons[0]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)

                try:
                    next_button.click()
                except:
                    driver.execute_script("arguments[0].click();", next_button)

                time.sleep(3)
                current_page += 1

            except Exception as e:
                print(f"Error navigating to next page: {e}")
                break

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

    product_name = extract_product_name_from_url(url)
    return reviews_data, product_name

def save_to_csv(reviews_data, product_name):
    filename = re.sub(r'[\\/*?:"<>|]', "", product_name)
    filename = f"reviews_{filename[:30]}_{time.strftime('%Y%m%d')}.csv"

    headers = ['Rating', 'Date', 'Title', 'Content', 'Reviewer', 'Verified', 'Brand Response']

    # Clean up newline characters for Excel compatibility
    for review in reviews_data:
        for key in review:
            if isinstance(review[key], str):
                review[key] = review[key].replace('\n', ' ').strip()

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(reviews_data)

    print(f"\n Reviews saved to: {filename}")
    return filename

if __name__ == "__main__":
    print("Starting Decathlon review scraper for multiple products...")

    for url in product_urls:
        print(f"\n🔗 Scraping: {url}")
        reviews_data, product_name = scrape_decathlon_reviews(url)

        if reviews_data:
            filename = save_to_csv(reviews_data, product_name)
            print(f" {len(reviews_data)} reviews saved to {filename}")
        else:
            print(" No reviews found or scraping failed for this product.")

