import pandas as pd
import plotly.express as px

# Load CSV file
df = pd.read_csv("/Users/courtashdale/Desktop/Sinatra/Sinatra-9/music-data/genres/genres_sheet.csv")

# Convert IDs to string
df["id"] = df["id"].astype(str)
df["parent_id"] = df["parent_id"].fillna("").astype(str)  # Convert NaN parent_id to empty string

# Merge to get parent genre names
df = df.merge(df[['id', 'genre']], left_on='parent_id', right_on='id', how='left', suffixes=('', '_parent'))

# Replace parent_id column with genre names
df['parent_genre'] = df['genre_parent'].fillna("")  # Fill NaN with empty string
df['genre'] = df['genre']  # Ensure genre names are in the correct column

# Plot Sunburst Chart
fig = px.sunburst(df, path=['parent_genre', 'genre'], title="Music Genre Hierarchy")

# Show Chart
fig.show()