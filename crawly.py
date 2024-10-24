import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def scroll_to_element(driver, element):
    """ Scroll to a specific element to make sure it's visible """
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(1)

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

    # List of potential button paths
    
    button_paths = [
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[7]/ul/li[1]/div/h2/button",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[6]/ul/li[1]/div/h2/button",
        "/html/body/div[1]/div/main/div[3]/section/div/div[2]/div/span[4]/div[8]/ul/li[1]/div/h2/button"
    ]
    
    # Corresponding description paths for the buttons
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
            # Try clicking the button to expand the description
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

            # Extract image URLs
            image_elements = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[1]/div/main/div[3]/section/div/div[1]/div/div[1]/ul/li/button/img"))
            )
            image_urls = [img.get_attribute('src') for img in image_elements]

            button_clicked = True
            break  # Stop after the first successful button click and description extraction

        except TimeoutException:
            print(f"Button with path {button_path} not found. Trying next path.")
    
    if not button_clicked:
        print("Description or images not found for all button paths. Skipping this product.")
        return product_name, price, None, None  # Return None for description and image_urls if none of the buttons work

    return product_name, price, description, image_urls


def scrape_multiple_products(chromedriver_path, url, output_file='datasets/shirts/shirts3.json', num_products=72, category="shirts"):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Enable headless mode if needed
    chrome_options.add_argument("--disable-gpu")  
    chrome_options.add_argument("--disable-webgl") 
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") 
    chrome_options.add_argument("--disable-extensions") 

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)

    driver.execute_script("window.scrollBy(0, 800);")  
    time.sleep(2)  

    # Prepare to save scraped data
    all_products_info = []

    for i in range(1, num_products + 1):
        time.sleep(2)

        # Dynamic Link
        product_link_xpath = f"/html/body/div[1]/div/main/div/div/div[1]/div[2]/div/div[1]/section/article[{i}]/a"

        try:
            product_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, product_link_xpath))
            )
            scroll_to_element(driver, product_link)  # Scroll to the product link
            product_url = product_link.get_attribute('href')
            product_link.click()  # Click to navigate to the product page
            print(f"Navigated to product {i}: {product_url}")
        
            # Scrape product info on the product page
            product_name, price, description, image_urls = scrape_product_info_on_page(driver, product_url)

            if description is None:  # If scraping fails, go back to the product listing page
                driver.back()
                continue

            # Append the product information to the list
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
            print(f"Product link for {i} not found. Skipping to the next product.")
        
        driver.back()
        
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, product_link_xpath)))

    # Save all product information to a JSON file
    with open(output_file, 'w') as file:
        json.dump(all_products_info, file, indent=4)

    print(f"Scraping of {num_products} products completed. Data saved to '{output_file}'.")

    # Close the browser
    driver.quit()

# Example usage:
# chromedriver_path = "/usr/local/bin/chromedriver"
chromedriver_path = "C:\\Program Files\\Executables\\chromedriver.exe"
url = "https://www.asos.com/men/shirts/cat/?cid=3602&page=3"  # URL of the shirts category
scrape_multiple_products(chromedriver_path, url, num_products=72)
