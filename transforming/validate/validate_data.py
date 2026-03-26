import pandas as pd

from transforming.config.constants import ALL_POSITIONS

def validate_data(df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        # Check sum of all position columns equals 1
        position_sum = sum(row.get(f"position__{pos}", 0) for pos in ALL_POSITIONS)
        if position_sum != 1:
            print(f'[WARNING] Row with match_id {row.get("match_id")} has invalid position encoding. Position sum: {position_sum}')
        
        # Check sum of all champion columns equals 1
        champion_sum = sum(value for key, value in row.items() if key.startswith("champion__"))
        if champion_sum != 1:
            print(f'[WARNING] Row with match_id {row.get("match_id")} has invalid champion encoding. Champion sum: {champion_sum}')

        # Check sum of all spell columns equals 2
        spell_sum = sum(value for key, value in row.items() if key.startswith("spell__"))
        if spell_sum != 2:
            print(f'[WARNING] Row with match_id {row.get("match_id")} has invalid spell encoding. Spell sum: {spell_sum}')
