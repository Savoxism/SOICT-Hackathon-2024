import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

from utils import scroll_to_element, get_image_sources_from_thumbnails

def scrape_product_info_on_page(driver, product_url):
    time.sleep(3) 
    driver.execute_script("window.scrollBy(0, 500);")  
    time.sleep(2)

    # Product name
    product_name_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[1]/h1"))
    )
    product_name = product_name_element.text

    # Price
    price_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[2]/div/span[2]"))
    )
    price = price_element.text
    
    button_paths = [
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/h2/button",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/h2/button",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/h2/button"
    ]
    
    # Corresponding paths
    ul_element_paths = [
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/div/div/div/ul",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/div/div/div/ul",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/div/div/div/ul"
    ]
    
    description = []
    image_urls = []
    button_clicked = False

    for button_path, ul_element_path in zip(button_paths, ul_element_paths):
        try:
            # Button that expands the product description
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, button_path))
            )
            button.click()
            time.sleep(3)

            # Extract the product description
            ul_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, ul_element_path))
            )
            li_elements = ul_element.find_elements(By.TAG_NAME, "li")
            description = [li.text for li in li_elements]

            # Extract all image URLs from the thumbnail list (ul)
            ul_xpath = "/html/body/div[1]/div/main/div[3]/section/div/div[1]/div/div[1]/ul"
            image_urls = get_image_sources_from_thumbnails(driver, ul_xpath)

            button_clicked = True
            break  

        except TimeoutException:
            print(f"Button with path {button_path} not found. Trying next path.")
    
    if not button_clicked:
        print("Description or images not found for all button paths. Skipping this product.")
        return product_name, price, None, None  

    return product_name, price, description, image_urls

def scrape_multiple_products(chromedriver_path, base_url, output_folder='datasets/shirts', start_page=2, num_products_per_page=72, max_pages=5, category="shirts"):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--disable-webgl") 
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
    chrome_options.add_argument("--disable-extensions") 

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    all_products_info = []
    current_page = start_page

    while current_page <= max_pages:
        url = f"{base_url}&page={current_page}"
        output_file = f"{output_folder}/shirts_{current_page}.json"
        print(f"Scraping page {current_page}: {url}")

        driver.get(url)
        driver.execute_script("window.scrollBy(0, 800);")  
        time.sleep(2)  

        for i in range(1, num_products_per_page + 1):
            time.sleep(2)
            # Dynamic Link
            product_link_xpath = f"/html/body/div[1]/div/main/div/div/div[1]/div[2]/div/div[1]/section/article[{i}]/a"

            try:
                product_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, product_link_xpath))
                )
                scroll_to_element(driver, product_link)  
                product_url = product_link.get_attribute('href')
                product_link.click()  
                print(f"Navigated to product {i} on page {current_page}: {product_url}")
            
                # Scrape product info on the product page
                product_name, price, description, image_urls = scrape_product_info_on_page(driver, product_url)

                if description is None: 
                    driver.back()
                    continue

                # Append the product info
                product_info = {
                    "product_url": product_url,
                    "product_name": product_name,
                    "price": price,
                    "category": category,
                    "description": description,
                    "product_imgs": image_urls
                }
                all_products_info.append(product_info)
            
            except TimeoutException:
                print(f"Product link for {i} not found on page {current_page}. Skipping to the next product.")
            
            driver.back()
            
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, product_link_xpath)))

        # Dump the data to a JSON file for the current page
        with open(output_file, 'w') as file:
            json.dump(all_products_info, file, indent=4)

        print(f"Scraping of {num_products_per_page} products from page {current_page} completed. Data saved to '{output_file}'.")

        # Clear product info for next page
        all_products_info = []

        # Move to the next page
        current_page += 1

    # Close the browser
    driver.quit()

# Example usage:
chromedriver_path = "/usr/local/bin/chromedriver"
# chromedriver_path = "C:\\Program Files\\Executables\\chromedriver.exe"
base_url = "https://www.asos.com/men/shirts/cat/?cid=3602"  # URL of the shirts category
scrape_multiple_products(chromedriver_path, base_url, num_products_per_page=72, max_pages=5)
