import time
import logging
from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging to see errors in Replit console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_driver():
    """Create and return a headless Chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Let Selenium find chromedriver in PATH (Replit's nix environment)
    return webdriver.Chrome(options=options)

def fetch_pawa_results():
    url = "https://www.betpawa.ug/virtual-sports?virtualTab=results"
    driver = None
    results = []
    try:
        logger.info("Starting driver...")
        driver = get_driver()
        logger.info(f"Fetching URL: {url}")
        driver.get(url)

        # Wait for the results table to appear
        logger.info("Waiting for results table...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "v-results-table"))
        )

        # Find all result rows
        rows = driver.find_elements(By.CLASS_NAME, "v-result-row")
        logger.info(f"Found {len(rows)} rows")

        # Process only the first 10 rows that contain "English"
        for row in rows[:10]:
            text = row.text
            if "English" in text:
                results.append(text.replace('\n', ' '))

        logger.info(f"Extracted {len(results)} results containing 'English'")

    except Exception as e:
        error_msg = f"Scraper Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        results.append(error_msg)
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed")
    return results

@app.route('/')
def home():
    matches = fetch_pawa_results()
    current_time = time.strftime('%H:%M:%S')
    source_url = "https://www.betpawa.ug/virtual-sports?virtualTab=results"

    # Minimal mobile-friendly HTML with a link to the source
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
        <p>Last Updated: {current_time}</p>
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
