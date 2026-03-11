import os
import re
import subprocess
import time
import urllib

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from src.logging import logger


def get_brave_major_version(brave_path: str = "/usr/bin/brave-browser") -> str:
    """Return the major version number of the installed Brave browser.

    e.g. '145' from 'Brave Browser 145.1.87.191'.
    """
    try:
        result = subprocess.run(
            [brave_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
        if match:
            return match.group(1)
    except Exception as e:
        logger.warning(f"Could not detect Brave version: {e}")
    return ""


def chrome_browser_options() -> Options:
    logger.debug("Setting Chrome browser options")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")  # Optional, useful in some environments
    options.add_argument("window-size=1200x800")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-autofill")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-animations")
    options.add_argument("--disable-cache")
    options.add_argument("--incognito")
    options.add_argument("--allow-file-access-from-files")  # Allow access to local files
    logger.debug("Using Chrome in incognito mode")

    return options


def init_browser() -> webdriver.Chrome:
    try:
        options = chrome_browser_options()
        brave_path = os.environ.get("BRAVE_PATH", "/usr/bin/brave-browser")
        if brave_path and os.path.exists(brave_path):
            options.binary_location = brave_path
            logger.debug(f"Using Brave browser at: {brave_path}")
            # Selenium Manager cannot detect ChromeDriver version from Brave
            # automatically, so read Brave's major version and pass it explicitly
            # to webdriver_manager to download the matching ChromeDriver.
            major = get_brave_major_version(brave_path)
            if major:
                logger.debug(f"Detected Brave major version: {major} — downloading matching ChromeDriver")
                service = ChromeService(ChromeDriverManager(driver_version=major).install())
            else:
                logger.warning("Could not detect Brave version; trying default ChromeDriver")
                service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
            logger.debug("Using default Chrome browser")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        logger.debug("Chrome browser initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize browser: {str(e)}")
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")


def html_to_pdf(html_content: str, driver: webdriver.Chrome) -> str:
    """Convert an HTML string to PDF and return it as a base64 string.

    Args:
        html_content: HTML string to convert.
        driver: Selenium Chrome WebDriver instance.

    Returns:
        Base64 encoded string of the generated PDF.

    Raises:
        ValueError: If the HTML input is not a valid string.
        RuntimeError: If a WebDriver exception occurs.
    """
    # Validate HTML content
    if not isinstance(html_content, str) or not html_content.strip():
        raise ValueError("HTML content must be a non-empty string.")

    # Encode the HTML into a data URL
    encoded_html = urllib.parse.quote(html_content)
    data_url = f"data:text/html;charset=utf-8,{encoded_html}"

    try:
        driver.get(data_url)
        # Wait for the page to fully load
        time.sleep(2)  # May need to increase for complex HTML

        # Execute the CDP command to print the page as PDF
        pdf_base64 = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,  # Include background in print
                "landscape": False,  # Portrait orientation
                "paperWidth": 8.27,  # A4 paper width in inches
                "paperHeight": 11.69,  # A4 paper height in inches
                "marginTop": 0.8,  # Top margin in inches (~2 cm)
                "marginBottom": 0.8,  # Bottom margin in inches (~2 cm)
                "marginLeft": 0.5,  # Left margin in inches (~1.27 cm)
                "marginRight": 0.5,  # Right margin in inches (~1.27 cm)
                "displayHeaderFooter": False,  # No headers or footers
                "preferCSSPageSize": True,  # Prefer CSS page size
                "generateDocumentOutline": False,  # No document outline
                "generateTaggedPDF": False,  # No tagged PDF
                "transferMode": "ReturnAsBase64",  # Return PDF as base64 string
            },
        )
        return pdf_base64["data"]
    except Exception as e:
        logger.error(f"WebDriver exception occurred: {e}")
        raise RuntimeError(f"WebDriver exception occurred: {e}")
