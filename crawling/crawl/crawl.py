import time
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from crawling.core.riot_client import RiotClient


PLAYERS_PAGE_URL = "https://op.gg/lol/spectate/list/pro-gamer?region=kr"

# ==============================================
# RIOT API - ACCOUNT
# ==============================================
# Function return:
# {
#     "puuid": "string",
#     "gameName": "string",
#     "tagLine": "string"
# }
# ==============================================
def get_account_by_riot_id(
    client: RiotClient,
    game_name: str,
    tag_line: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    encoded_game_name = quote(game_name, safe="")
    encoded_tag_line = quote(tag_line, safe="")
    path = f"/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
    return client.get(path, base_url=base_url)


# ==============================================
# RIOT API - MATCH
# ==============================================
# Function return:
# [
#     "string"
# ]
# ==============================================
def get_match_ids(
    client: RiotClient,
    puuid: str,
    count: int = 5,
    base_url: str | None = None,
) -> list[str]:
    path = f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids"
    remaining = max(0, int(count))
    start = 0
    all_match_ids: list[str] = []

    # Riot match-v5 supports max 100 per request, so we page large requests.
    while remaining > 0:
        batch_size = min(100, remaining)
        params = {"start": start, "count": batch_size}
        batch = client.get(path, params=params, base_url=base_url)

        if not isinstance(batch, list):
            break

        all_match_ids.extend(batch)
        received = len(batch)

        if received < batch_size:
            # No more matches available.
            break

        start += received
        remaining -= received

    return all_match_ids

# ==============================================
# RIOT API - MATCH DETAIL
# ==============================================
# Function return:
# {
#     "metadata": {
#         "matchId": "string",
#         ...
#     }
#     "info": {
#         "gameId": 1234567890,
#         "queueId": 420,           (e.g. 420 for Ranked Solo/Duo, Refer to the Game Constants documentation..)
#         "participants": [
#             {
#                 "puuid": "string",
#                 "championName": "string",
#                 "summoner1Id": int,           (e.g. 4 for Flash, 14 for Ignite, etc.)
#                 "summoner2Id": int,           (e.g. 4 for Flash, 14 for Ignite, etc.)
#                 "teamPosition": "string",     (e.g. TOP, JUNGLE, MID, ADC, SUPPORT)
#                 "kills": int,
#                 "deaths": int,
#                 "assists": int,
#                 "win": bool,
#                 ...
#             },
#             ...
#         ]
#     }
# }
# ==============================================
def get_match_detail(
    client: RiotClient,
    match_id: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    path = f"/lol/match/v5/matches/{quote(match_id, safe='')}"
    return client.get(path, base_url=base_url)



# ==============================================
# RIOT API - MATCH TIMELINE
# ==============================================
# Function return:
# {
#     "metadata": {
#         ...
#     }
#     "info": {
#         "participants": [
#             {
#                 "puuid": "string",
#                 "participantId": int,      (1-10, where 1-5 are one team and 6-10 are the other team)
#             }
#         ],
#         "frames": [
#             {
#                 "events": [
#                     {
#                         "type": "ITEM_PURCHASED",     (e.g. ITEM_PURCHASED, CHAMPION_KILL, etc.)
#                         "participantId": int,         (1-10, where 1-5 are one team and 6-10 are the other team)
#                         "itemId": int,                (e.g. 1055 for Doran's Blade, etc.)
#                         "timestamp": int,             (milliseconds since game start)
#                         ...                           (other fields depending on event type, e.g. killerId, victimId for CHAMPION_KILL)
#                     },
#                     {
#                         "type": "ITEM_DESTROYED",     (e.g. ITEM_PURCHASED, CHAMPION_KILL, etc.)
#                         "participantId": int,         (1-10, where 1-5 are one team and 6-10 are the other team)
#                         "itemId": int,                (e.g. 1055 for Doran's Blade, etc.)
#                         "timestamp": int,             (milliseconds since game start)
#                         ...                           (other fields depending on event type, e.g. killerId, victimId for CHAMPION_KILL)
#                     }
#                 ]
#             }
#         ]
#     }
# }

def get_match_timeline(
    client: RiotClient,
    match_id: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    path = f"/lol/match/v5/matches/{quote(match_id, safe='')}/timeline"
    return client.get(path, base_url=base_url)





# ==============================================
# CRAWL PLAYER 
# ==============================================
# Function return:
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
#
# File return: kr.txt
# File structure:
# player_name1    player_link1
# player_name2    player_link2
# ...
#
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


def _crawl_players():
    url = PLAYERS_PAGE_URL
    print(f"Crawling: {url}")

    driver = _create_chrome_driver()

    try:
        driver.get(url)
        time.sleep(5)

        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        html = driver.page_source

    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    players = soup.select("a[href*='/summoners/']")

    result = []
    for p in players:
        name = p.get_text(strip=True)
        link = p.get("href")

        if name and link:
            if link.startswith("/"):
                link = "https://op.gg" + link

            result.append({
                "name": name,
                "link": link
            })

    print(f"Found {len(result)} players")
    return result


def crawl_players():
    players = []

    try:
        players = _crawl_players()
    except Exception as e:
        print(f"Error crawling players: {e}")
        return players
    time.sleep(5)
    return players