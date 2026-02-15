import time
import logging
import threading
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global cache for results
cached_results = []
last_update = None
cache_lock = threading.Lock()

def get_driver():
    """Create and return a headless Chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def fetch_pawa_results():
    """Scrape results and return list of strings."""
    url = "https://www.betpawa.ug/virtual-sports?virtualTab=results"
    driver = None
    results = []
    try:
        logger.info("Starting driver for background update...")
        driver = get_driver()
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "v-results-table"))
        )
        rows = driver.find_elements(By.CLASS_NAME, "v-result-row")
        logger.info(f"Found {len(rows)} rows")
        for row in rows[:10]:
            text = row.text
            if "English" in text:
                results.append(text.replace('\n', ' '))
        logger.info(f"Extracted {len(results)} results")
    except Exception as e:
        logger.error(f"Scraper error: {e}", exc_info=True)
        results.append(f"Scraper Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
    return results

def update_cache():
    """Background task to update cached results."""
    global cached_results, last_update
    while True:
        logger.info("Running background update...")
        new_results = fetch_pawa_results()
        with cache_lock:
            cached_results = new_results
            last_update = time.strftime('%H:%M:%S')
        logger.info("Cache updated")
        time.sleep(60)  # Update every 60 seconds

# Start background thread
thread = threading.Thread(target=update_cache, daemon=True)
thread.start()
# Give the first scrape a chance to complete before first request
time.sleep(5)

@app.route('/')
def home():
    with cache_lock:
        matches = cached_results.copy() if cached_results else ["Loading results..."]
        update_time = last_update if last_update else "Not yet updated"

    source_url = "https://www.betpawa.ug/virtual-sports?virtualTab=results"

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #121212; color: white; font-family: sans-serif; padding: 20px; }}
            .match {{ background: #1e1e1e; padding: 10px; margin-bottom: 5px; border-radius: 5px; border-left: 4px solid #00ff00; }}
            h1 {{ color: #00ff00; }}
            .source-link {{
                display: inline-block;
                margin: 10px 0;
                padding: 8px 12px;
                background: #333;
                color: #00ff00;
                text-decoration: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            .source-link:hover {{ background: #444; }}
        </style>
    </head>
    <body>
        <h1>NBX Live Results</h1>
        <p>Last Updated: {update_time}</p>
        <a class="source-link" href="{source_url}" target="_blank" rel="noopener noreferrer">
            🔗 View on BetPawa
        </a>
        {''.join([f'<div class="match">{m}</div>' for m in matches])}
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
