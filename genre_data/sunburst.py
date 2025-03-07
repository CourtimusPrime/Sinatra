import pandas as pd
import json
import matplotlib.pyplot as plt
import plotly.express as px
import ace_tools as tools  # For displaying data in the chat

# Load CSV
csv_file = "genres_mar6_noval.csv"
df = pd.read_csv(csv_file)

# Receive genre counts from JavaScript (Assuming JSON input)
genre_counts_json = '''{
    "pop": 15,
    "hip hop": 10,
    "indie rock": 8,
    "electronic": 7
}'''  # Example JSON input, replace with actual incoming data

genre_counts = json.loads(genre_counts_json)

# Update the CSV genre values
df["count"] = df["genre"].map(genre_counts).fillna(0).astype(int)

# Save updated CSV
df.to_csv(csv_file, index=False)

# Filter non-zero values for visualization
df_filtered = df[df["count"] > 0]

# Show the updated DataFrame
tools.display_dataframe_to_user(name="Updated Genre Counts", dataframe=df_filtered)

# Generate Sunburst Chart
fig = px.sunburst(df_filtered, path=["genre"], values="count", title="Top 100 Track Genres (Sunburst Chart)")

# Show the chart
fig.show()