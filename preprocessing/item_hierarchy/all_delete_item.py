from __future__ import annotations

import json
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from preprocessing.config.constants import (
    PREPROCESS_DATA_DIR,
    PREPROCESS_REMOVED_ITEMS_PATH,
    TARGET_SECTIONS,
    WIKI_ITEMS_URL,
)


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def fetch_rendered_html(url: str) -> str:
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(6)
        return str(driver.page_source)
    finally:
        driver.quit()


def _normalize_space(text: str | None) -> str:
    return " ".join((text or "").split())


def _extract_section_item_names(soup: BeautifulSoup, section_name: str) -> list[str]:
    section_name_normalized = _normalize_space(section_name).lower()

    section_dt = soup.find(
        "dt",
        string=lambda s: _normalize_space(s).lower() == section_name_normalized,
    )
    if section_dt is None:
        return []

    section_block = section_dt.find_parent("dl")
    if section_block is None:
        return []

    list_container = section_block.find_next_sibling("div")
    if list_container is None:
        return []

    names: list[str] = []
    seen: set[str] = set()

    for node in list_container.select("[data-item]"):
        name = _normalize_space(node.get("data-item"))
        if not name:
            continue

        key = name.lower()
        if key in seen:
            continue

        seen.add(key)
        names.append(name)

    return names


def extract_target_sections(
    html: str,
    target_sections: list[str] = TARGET_SECTIONS,
) -> dict[str, object]:
    soup = BeautifulSoup(html, "lxml")

    by_section: dict[str, list[str]] = {}
    merged_names: list[str] = []
    merged_seen: set[str] = set()

    for section_name in target_sections:
        section_items = _extract_section_item_names(soup, section_name)
        by_section[section_name] = section_items

        for name in section_items:
            key = name.lower()
            if key in merged_seen:
                continue
            merged_seen.add(key)
            merged_names.append(name)

    return {
        "by_section": by_section,
        "all_unique_items": merged_names,
    }


def save_removed_items(payload: list[str], output_path: str = str(PREPROCESS_REMOVED_ITEMS_PATH)) -> None:
    PREPROCESS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def fetch_removed_items() -> None:
    html = fetch_rendered_html(WIKI_ITEMS_URL)
    payload = extract_target_sections(html)
    all_unique_items = payload["all_unique_items"]

    if not all_unique_items:
        raise RuntimeError("Could not find any item in the target sections.")
    save_removed_items(all_unique_items)
