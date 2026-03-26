import pandas as pd


data_path = "data/preprocess/matches_preprocessed.parquet"
transform_data_path = "data/transform/matches_encoded.parquet"

df = pd.read_parquet(transform_data_path)

# Explore the preprocessed data
""" print(df.head())
print(df.info())
print(df.describe())
print(df.columns)
print(df.isnull().sum())
 """
def count_interactions(df):
    # Sum all the table
    columns = df.columns[1:]  # Exclude the first column (e.g., match_id)
    total_interactions = df[columns].sum().sum()
    return total_interactions

total_interactions = count_interactions(df)
print(f"Total interactions in the dataset: {total_interactions}")

