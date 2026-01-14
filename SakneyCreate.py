import pandas as pd
import plotly.graph_objects as go

# 1. LOAD DATA
# Replace with your actual filename if different
file_path = '251208_OfficeTrackApplications.csv'
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: File '{file_path}' not found. Please check the filename.")
    exit()

# 2. DATA CLEANING & PREPARATION
# Standardize status values for cleaner labels
df['Applied_Label'] = df['Application Status'].astype(str).fillna('Unknown')

# Handle First Response: Fill NaNs with 'Pending' if the application was sent
df['Response_Label'] = df['First Response Result'].fillna('Pending')

# Handle missing 'Country' values, replacing with 'Various'
df['Country_Label'] = df['Country'].fillna('Various')


# 3. BUILD SANKEY NODES AND LINKS (Revised Order)
# We need lists of labels, sources, targets, and values.
labels = []
source_indices = []
target_indices = []
values = []

# Helper function to get or create a node index
def get_node_index(label):
    if label not in labels:
        labels.append(label)
    return labels.index(label)

# --- FLOW 1: Country -> Company Prestige ---
country_prestige_counts = df.groupby(['Country_Label', 'Company Prestige']).size().reset_index(name='count')
for index, row in country_prestige_counts.iterrows():
    src_idx = get_node_index(row['Country_Label'])
    tgt_idx = get_node_index(row['Company Prestige'])
    source_indices.append(src_idx)
    target_indices.append(tgt_idx)
    values.append(row['count'])

# --- FLOW 2: Company Prestige -> Total Opportunities ---
# Calculate total opportunities per prestige level to flow into the 'Total Opportunities' node
prestige_counts = df['Company Prestige'].value_counts()
for prestige, count in prestige_counts.items():
    src_idx = get_node_index(prestige)
    tgt_idx = get_node_index("Total Opportunities") # This node acts as a central hub
    source_indices.append(src_idx)
    target_indices.append(tgt_idx)
    values.append(count)

# --- FLOW 3: Total Opportunities -> Application Status ---
# Get total counts for each Application Status, flowing from the central 'Total Opportunities' node
status_counts = df['Applied_Label'].value_counts()
for status, count in status_counts.items():
    src_idx = get_node_index("Total Opportunities")
    tgt_idx = get_node_index(status)
    source_indices.append(src_idx)
    target_indices.append(tgt_idx)
    values.append(count)

# --- FLOW 4: Applied -> First Response ---
# We only track responses for those who actually 'Applied'
applied_df = df[df['Applied_Label'] == 'Applied']
response_counts = applied_df['Response_Label'].value_counts()

for response, count in response_counts.items():
    # Source is 'Applied' node (created in Flow 3)
    src_idx = get_node_index("Applied")

    # Target is the specific response (e.g., 'Pending', 'negative')
    response_clean = str(response)
    if response_clean == "Negative":
        response_clean = "Negative Response"
    elif response_clean == "Pending":
        response_clean = "Response Pending"

    tgt_idx = get_node_index(response_clean)

    source_indices.append(src_idx)
    target_indices.append(tgt_idx)
    values.append(count)

# 4. CREATE FIGURE
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels,
        color="blue"
    ),
    link=dict(
        source=source_indices,
        target=target_indices,
        value=values,
        # You can customize colors here if you want specific flows to be red/green
    )
)])

fig.update_layout(title_text="Job Application Progress", font_size=12)

# Show and Save
fig.show()
fig.write_html("job_application_sankey.html")
print("Sankey diagram saved to 'job_application_sankey.html'")