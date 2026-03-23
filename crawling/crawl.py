from crawling.config import CRAWL_REGION
from utils.output import (
    save_players_crawl_summary, 
    save_players_to_file, 
    save_matches_to_file, 
    save_matches_crawl_summary 
)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from html import unescape

from bs4 import BeautifulSoup


PLAYERS_PAGE_URL = "https://op.gg/lol/spectate/list/pro-gamer?region={}"


# ==============================================
# UTILS FUNCTION
# ==============================================

def _create_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def _click_all_show_more(driver, max_clicks=200):
    clicks = 0
    while clicks < max_clicks:
        buttons = driver.find_elements(By.XPATH, "//button[normalize-space()='Show more']")

        target = None
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                target = button
                break

        if target is None:
            break

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            target.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", target)
            except Exception:
                break

        clicks += 1
        time.sleep(3)

    return clicks


def _click_all_show_more_detail_games(driver, max_clicks=500):
    clicks = 0
    index = 0

    while clicks < max_clicks:
        buttons = driver.find_elements(
            By.XPATH,
            "//button[.//span[normalize-space()='Show More Detail Games']]"
        )

        if index >= len(buttons):
            break

        target = buttons[index]
        index += 1

        if not target.is_displayed() or not target.is_enabled():
            continue

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            target.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            try:
                driver.execute_script("arguments[0].click();", target)
            except Exception:
                continue

        clicks += 1
        time.sleep(1)

    return clicks


# ==============================================
# CRAWL PLAYER 
# crawl_players = {
#     "kr": [
#         {
#             "name": "player1",
#             "link": "https://op.gg/summoners/kr/player1"
#         },
#         ...
#     ],
#     ...
# }
# ==============================================

def _crawl_players_by_region(region="kr"):
    url = PLAYERS_PAGE_URL.format(region)
    print(f"Crawling: {url}")

    driver = _create_chrome_driver()

    try:
        driver.get(url)

        # ⏳ đợi JS load
        time.sleep(5)

        # 🔽 scroll để load thêm data
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # 📄 lấy HTML sau khi render
        html = driver.page_source

    finally:
        driver.quit()

    # 🧠 parse bằng BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    players = soup.select("a[href*='/summoners/']")

    result = []
    for p in players:
        name = p.get_text(strip=True)
        link = p.get("href")

        if name and link:
            # fix link relative
            if link.startswith("/"):
                link = "https://op.gg" + link

            result.append({
                "name": name,
                "link": link
            })

    print(f"Found {len(result)} players")

    return result


def crawl_players():
    summary = []
    crawl_players = {region: [] for region in CRAWL_REGION}
    for region in CRAWL_REGION:
        try:
            players = _crawl_players_by_region(region)
            crawl_players[region].extend(players)
        except Exception as e:
            print(f"Error crawling region {region}: {e}")
            summary.append({
                "region": region,
                "count": 0,
                "status": f"error: {e}"
            })
            continue
        save_players_to_file(players, region)
        summary.append({
            "region": region,
            "count": len(players),
            "status": "success"
        })
        time.sleep(5)
    save_players_crawl_summary(summary)
    return crawl_players

# ==============================================
# CRAWL MATCH HISTORY 
# ==============================================

def _extract_match_urls_v2(page_source):
    urls = set()
    soup = BeautifulSoup(page_source, "html.parser")
    for input_tag in soup.find_all("input", attrs={"readonly": True, "value": True}):
        url = input_tag.get("value")
        if url and "/summoners/" in url and "/matches/" in url:
            full_url = unescape(url).strip().strip('"\'').replace("\\/", "/")
            if full_url.startswith("/"):
                full_url = "https://op.gg" + full_url
            if full_url.startswith("http"):
                urls.add(full_url)
    return list(urls)

def crawl_match_history_by_player_url(player_url, driver=None, wait=None, wait_timeout=20, verbose=False):
    if not player_url:
        return []

    if player_url.startswith("/"):
        player_url = "https://op.gg" + player_url

    owns_driver = driver is None
    if owns_driver:
        driver = _create_chrome_driver()

    if wait is None:
        wait = WebDriverWait(driver, wait_timeout)

    try:
        driver.get(player_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)

        clicked_show_more = _click_all_show_more(driver)
        clicked_detail = _click_all_show_more_detail_games(driver)
        time.sleep(5)

        match_urls = _extract_match_urls_v2(driver.page_source)

        if verbose:
            print(
                f"[crawl_match_history_by_player_url] "
                f"clicked_show_more={clicked_show_more}, "
                f"clicked_detail_games={clicked_detail}, "
                f"extracted_match_urls={len(match_urls)}"
            )

        return match_urls
    except Exception as e:
        print(f"Error crawling match history for {player_url}: {e}")
        return []
    finally:
        if owns_driver:
            driver.quit()


def crawl_players_match_history(players):
    if not isinstance(players, dict):
        raise ValueError("players must be a dict with region keys: {'region': [{'player', 'player_url'}]}")

    driver = _create_chrome_driver()
    wait = WebDriverWait(driver, 20)
    result = []
    summary = {}

    try:
        for region, player_list in players.items():
            for idx, item in enumerate(player_list, start=1):
                player = item.get("player") or item.get("name") or ""
                player_url = item.get("player_url") or item.get("url") or item.get("link") or ""

                if not player_url:
                    result.append({"player": player, "matches": []})
                    continue

                if player_url.startswith("/"):
                    player_url = "https://op.gg" + player_url

                print(f"[{idx}/{len(players)}] Crawling match history: {player} -> {player_url}")

                try:
                    matches = crawl_match_history_by_player_url(
                        player_url=player_url,
                        driver=driver,
                        wait=wait
                    )
                    save_matches_to_file(player, matches)
                    result.append({
                        "player": player,
                        "matches": matches
                    })
                except Exception as e:
                    print(f"Error crawling match history for {player}: {e}")
                    result.append({
                        "player": player,
                        "matches": []
                    })
                
            match_count = sum(len(r.get("matches", [])) for r in result)
            summary[region] = {
                "match_count": match_count,
            }
        save_matches_crawl_summary(summary)
    finally:
        driver.quit()

    return result


# ==============================================
# CRAWL MATCH DETAIL
# ==============================================