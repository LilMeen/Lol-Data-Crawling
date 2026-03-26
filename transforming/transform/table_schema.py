import ast
from collections.abc import Iterable

import numpy as np
import pandas as pd

from transforming.config.constants import ALL_CHAMPIONS, ALL_POSITIONS, ALL_SPELLS


def _normalize_text(value: object) -> str:
	return str(value or "").strip()


def _normalize_key(value: object) -> str:
	return _normalize_text(value).lower()


def _normalize_spell(value: object) -> str:
	return _normalize_text(value).title()


def _to_string_list(value: object) -> list[str]:
	if value is None:
		return []

	if isinstance(value, str):
		text = value.strip()
		if not text:
			return []

		# Some parquet/CSV round-trips can turn list columns into string literals.
		if text.startswith("[") and text.endswith("]"):
			try:
				parsed = ast.literal_eval(text)
				return _to_string_list(parsed)
			except (ValueError, SyntaxError):
				pass

		return [text]

	if isinstance(value, list):
		return [_normalize_text(item) for item in value if _normalize_text(item)]
	if isinstance(value, tuple):
		return [_normalize_text(item) for item in value if _normalize_text(item)]
	if isinstance(value, set):
		return [_normalize_text(item) for item in value if _normalize_text(item)]

	if isinstance(value, Iterable) and not isinstance(value, (dict, bytes, bytearray)):
		return [_normalize_text(item) for item in value if _normalize_text(item)]

	return []



def _build_encoded_columns(
	records_df: pd.DataFrame,
	item_names: Iterable[str],
	max_item_length: int,
) -> pd.DataFrame:
	champion_map = {_normalize_key(name): name for name in ALL_CHAMPIONS}
	spell_map = {_normalize_spell(name): name for name in ALL_SPELLS}

	item_names_sorted = sorted({_normalize_text(name) for name in item_names if _normalize_text(name)})
	position_columns = [f"position__{position}" for position in ALL_POSITIONS]
	champion_columns = [f"champion__{champion}" for champion in ALL_CHAMPIONS]
	spell_columns = [f"spell__{spell}" for spell in ALL_SPELLS]
	item_columns = [
		f"item__{item_name}__{order}"
		for item_name in item_names_sorted
		for order in range(1, max_item_length + 1)
	]
	feature_columns = position_columns + champion_columns + spell_columns + item_columns
	feature_index = {column_name: idx for idx, column_name in enumerate(feature_columns)}

	feature_matrix = np.zeros((len(records_df), len(feature_columns)), dtype=np.uint8)
	match_ids: list[str] = []

	for row_idx, (_, row) in enumerate(records_df.iterrows()):
		match_ids.append(_normalize_text(row.get("player")) + "__" + _normalize_text(row.get("matchId")))

		position_value = _normalize_text(row.get("position"))
		position_column = f"position__{position_value}"
		position_col_idx = feature_index.get(position_column)
		if position_col_idx is not None:
			feature_matrix[row_idx, position_col_idx] = 1

		champion_key = _normalize_key(row.get("champion"))
		champion_original = champion_map.get(champion_key)
		if champion_original:
			champion_col_idx = feature_index.get(f"champion__{champion_original}")
			if champion_col_idx is not None:
				feature_matrix[row_idx, champion_col_idx] = 1

		for spell in _to_string_list(row.get("spell")):
			spell_original = spell_map.get(_normalize_spell(spell))
			if spell_original:
				spell_col_idx = feature_index.get(f"spell__{spell_original}")
				if spell_col_idx is not None:
					feature_matrix[row_idx, spell_col_idx] = 1

		full_builds = _to_string_list(row.get("fullBuilds"))
		for order, item_name in enumerate(full_builds, start=1):
			if order > max_item_length:
				break
			normalized_item = _normalize_text(item_name)
			if not normalized_item:
				continue
			item_col_idx = feature_index.get(f"item__{normalized_item}__{order}")
			if item_col_idx is not None:
				feature_matrix[row_idx, item_col_idx] = 1
	
	print("Total positions:", len(ALL_POSITIONS))
	print("Total champions:", len(ALL_CHAMPIONS))
	print("Total spells:", len(ALL_SPELLS))
	print("Total items:", len(item_names))
	print("Max item length:", max_item_length)
	print("== Encoded Columns ==")
	print("Total encoded columns = positions + champions + spells + (items * max_item_length) = {0}".format(
		len(ALL_POSITIONS) + len(ALL_CHAMPIONS) + len(ALL_SPELLS) + (len(item_names) * max_item_length)
	))
	print("Actual encoded columns:", len(feature_columns) + 1)

	encoded_df = pd.DataFrame(feature_matrix, columns=feature_columns)
	encoded_df.insert(0, "match_id", match_ids)
	return encoded_df


def build_training_table(
	records_df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
	"""
	Build the final one-hot encoded table from crawled match records.

	Input records are expected to follow the crawl JSON schema and already be in a DataFrame.
	"""
	data = records_df.copy()
	if "fullBuilds" not in data.columns:
		raise ValueError(
			"Missing 'fullBuilds' column in transforming input. "
			"Run preprocessing first to generate full build sequence."
		)

	data["fullBuilds"] = data["fullBuilds"].apply(_to_string_list)
	max_item_length = int(data["fullBuilds"].apply(len).max()) if not data.empty else 0
	item_names = {
		_normalize_text(item)
		for build in data["fullBuilds"]
		for item in build
		if _normalize_text(item)
	}

	encoded_df = _build_encoded_columns(
		records_df=data,
		item_names=item_names,
		max_item_length=max_item_length,
	)
	return encoded_df, max_item_length
