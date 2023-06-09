from urllib.parse import urljoin 

from apify import Actor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

async def main():
    async with Actor:

        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get("start_urls", [{"url": "https://apify.com"}])
        max_depth = actor_input.get("max_depth", 1)

        if not start_urls:
            Actor.log.info("No start URLs specified in actor input, exiting...")
            await Actor.exit()

        # Enqueue the starting URLs in the default request queue
        default_queue = await Actor.open_request_queue()
        for start_url in start_urls:
            url = start_url.get("url")
            Actor.log.info(f"Enqueuing {url} ...")
            await default_queue.add_request({"url": url, "userData": {"depth": 0}})

        # Launch a new Selenium Chrome WebDriver
        Actor.log.info("Launching Chrome WebDriver...")
        chrome_options = ChromeOptions()
        if Actor.config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options = chrome_options)

        print("wtf my code")

        driver.get("http://www.example.com")
        assert driver.title == "Example Domain"

        # Process the requests in the queue one by one
        while request := await default_queue.fetch_next_request():
            url = request["url"]
            depth = request["userData"]["depth"]
            Actor.log.info(f"Scraping {url} ...")

            try:
                driver.get(url)
                if depth < max_depth:
                    for link in driver.find_elements(By.TAG_NAME, "a"):
                        link_href = link.get_attribute("href")
                        link_url = urljoin(url, link_href)
                        if link_url.startswith(("http://", "https://")):
                            Actor.log.info(f"Enqueuing {link_url} ...")
                            await default_queue.add_request({
                                "url": link_url,
                                "userData": {"depth": depth + 1}
                            })
                title = driver.title
                await Actor.push_data({"url": url, "title": title})
            except:
                Actor.log.exception(f"Cannot extract data from {url}.")
            finally:
                await default_queue.mark_request_as_handled(request)
        driver.quit()
