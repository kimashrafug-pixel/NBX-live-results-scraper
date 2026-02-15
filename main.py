import time
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Use standard Replit path for chromedriver
    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def fetch_pawa_results():
    url = "https://www.betpawa.ug/virtual-sports?virtualTab=results"
    driver = get_driver()
    results = []
    try:
        driver.get(url)
        # Wait for the table to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "v-results-table"))
        )
        rows = driver.find_elements(By.CLASS_NAME, "v-result-row")
        for row in rows[:10]:
            if "English" in row.text:
                results.append(row.text.replace('\n', ' '))
    except Exception as e:
        results.append(f"Scraper Error: {str(e)}")
    finally:
        driver.quit()
    return results

@app.route('/')
def home():
    matches = fetch_pawa_results()
    current_time = time.strftime('%H:%M:%S')
    
    # Minimal mobile-friendly HTML
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #121212; color: white; font-family: sans-serif; padding: 20px; }}
            .match {{ background: #1e1e1e; padding: 10px; margin-bottom: 5px; border-radius: 5px; border-left: 4px solid #00ff00; }}
            h1 {{ color: #00ff00; }}
        </style>
    </head>
    <body>
        <h1>NBX Live Results</h1>
        <p>Last Updated: {current_time}</p>
        {''.join([f'<div class="match">{m}</div>' for m in matches])}
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
