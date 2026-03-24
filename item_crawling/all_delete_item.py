import json
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


WIKI_ITEMS_URL = "https://wiki.leagueoflegends.com/en-us/List_of_items"
OUTPUT_PATH = Path(__file__).with_name("removed_items.json")

TARGET_SECTIONS = [
	"Removed items",
	"Arena exclusive items",
	"Arena Anvil items",
	"Arena Prismatic items",
	"Minion and Turret items",
	"Champion exclusive items",
]


def create_driver():
	options = webdriver.ChromeOptions()
	options.add_argument("--headless=new")
	options.add_argument("--disable-blink-features=AutomationControlled")
	options.add_argument("--no-sandbox")
	options.add_argument("--disable-dev-shm-usage")

	return webdriver.Chrome(
		service=Service(ChromeDriverManager().install()),
		options=options,
	)


def fetch_rendered_html(url):
	driver = create_driver()
	try:
		driver.get(url)
		time.sleep(6)
		return driver.page_source
	finally:
		driver.quit()


def _normalize_space(text):
	return " ".join((text or "").split())


def _extract_section_item_names(soup, section_name):
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

	names = []
	seen = set()

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


def extract_target_sections(html, target_sections=TARGET_SECTIONS):
	soup = BeautifulSoup(html, "lxml")

	by_section = {}
	merged_names = []
	merged_seen = set()

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


def save_removed_items(payload, output_path=OUTPUT_PATH):
	with open(output_path, "w", encoding="utf-8") as file:
		json.dump(payload, file, ensure_ascii=False, indent=2)


def main():
	html = fetch_rendered_html(WIKI_ITEMS_URL)
	payload = extract_target_sections(html)
	all_unique_items = payload["all_unique_items"]
	by_section = payload["by_section"]

	if not all_unique_items:
		raise RuntimeError("Could not find any item in the target sections.")

	save_removed_items(all_unique_items)

	for section_name in TARGET_SECTIONS:
		print(f"{section_name}: {len(by_section.get(section_name, []))} items")
	print(f"All unique items across target sections: {len(all_unique_items)}")
	print(f"Saved to {OUTPUT_PATH}")
	print("Sample:", all_unique_items[:10])


if __name__ == "__main__":
	main()
