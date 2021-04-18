# %%
import pandas as pd
from pathlib import Path


tops_files_path = Path('./data/tops/')
combined_tops_df = pd.DataFrame()

# Get all tops in one dataframe
for file in tops_files_path.glob("*.csv"):
    df = pd.read_csv(file)
    name = file.stem
    df['UWI'] = name
    combined_tops_df = pd.concat([combined_tops_df, df])

# reorder and rename columns
combined_tops_df = combined_tops_df.reindex(columns=['UWI', ' Comp formation', 'top'])
combined_tops_df.columns = ['UWI', 'top_name', 'MD']
combined_tops_df.to_csv(tops_files_path / 'tops_data.csv', index=False)
print(combined_tops_df)


# %%
