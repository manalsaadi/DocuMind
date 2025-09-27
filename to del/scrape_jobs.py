from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_huggingface_jobs(driver):
    url = "https://huggingface.co/about#careers"
    driver.get(url)

    # Attendre que les sections carrières soient chargées (exemple CSS d'un container de job)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/jobs/']"))
        )
    except:
        print("Jobs section did not load in time.")
        return []

    jobs = []
    anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']")
    for a in anchors:
        title = a.text.strip()
        link = a.get_attribute("href")
        # Pour lieu et date, ça dépend des pages spécifiques, ici pas affiché directement
        jobs.append({"company": "HuggingFace", "title": title, "location": "", "date": "", "link": link})
    return jobs

def main():
    driver = setup_driver()
    all_jobs = []

    hf_jobs = scrape_huggingface_jobs(driver)
    all_jobs.extend(hf_jobs)

    driver.quit()

    if not all_jobs:
        print("No jobs found.")
        return

    df = pd.DataFrame(all_jobs)
    df.to_csv("jobs_selenium.csv", index=False)
    print(f"Saved {len(df)} jobs to jobs_selenium.csv")

if __name__ == "__main__":
    main()
