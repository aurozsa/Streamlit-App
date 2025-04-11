import pandas as pd
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from io import BytesIO
import streamlit as st

# Load baby name data directly from the SSA website
@st.cache_data
def load_name_data():
    names_url = 'https://www.ssa.gov/oact/babynames/names.zip'
    response = requests.get(names_url)
    
    # Extract and process the ZIP file
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        dfs = []
        files = [file for file in z.namelist() if file.endswith('.txt')]
        for file in files:
            with z.open(file) as f:
                df = pd.read_csv(f, header=None)
                df.columns = ['name', 'sex', 'count']
                df['year'] = int(file[3:7])  # Extract year from file name
                dfs.append(df)
        data = pd.concat(dfs, ignore_index=True)
    
    # Calculate proportions within each year/sex group
    data['pct'] = data['count'] / data.groupby(['year', 'sex'])['count'].transform('sum')
    return data

# Load data
df = load_name_data()

# Add additional columns for total births and proportions
df['total_births'] = df.groupby(['year', 'sex'])['count'].transform('sum')
df['prop'] = df['count'] / df['total_births']

# Streamlit app layout
st.title('Baby Name Popularity App')

# Instructions for first-time visitors
st.markdown("""
### How to Use This App:
- Enter a name below to explore its popularity over time.
- Use the sidebar to filter by gender or year range.
- Check out the **Graphs** tab for visualizations and the **Data Summaries** tab for additional insights.
""")

# Main input widget: Name entry
name_of_interest = st.text_input('Enter a name:', placeholder="e.g., John")

# Sidebar implementation for additional input widgets
st.sidebar.title("Filter Options")
plot_female = st.sidebar.checkbox('Plot Female', value=True)
plot_male = st.sidebar.checkbox('Plot Male', value=True)
year_range = st.sidebar.slider(
    'Filter by Year Range',
    min_value=int(df['year'].min()),
    max_value=int(df['year'].max()),
    value=(1900, 2000)
)

# Filter data for the entered name and year range
filtered_data = df[(df['year'].between(year_range[0], year_range[1])) & 
                   (df['name'].str.lower() == name_of_interest.lower())]

# Tabs for organization
tab1, tab2 = st.tabs(["Graphs", "Data Summaries"])

with tab1:
    st.header(f'Popularity Trends for "{name_of_interest}"')

    # Plot trends for female and male
    fig1 = plt.figure(figsize=(15, 8))
    if plot_female:
        sns.lineplot(data=filtered_data[filtered_data['sex'] == 'F'], x='year', y='prop', label='Female', color='red')
    if plot_male:
        sns.lineplot(data=filtered_data[filtered_data['sex'] == 'M'], x='year', y='prop', label='Male', color='blue')
    plt.title(f'Popularity of "{name_of_interest}" Over Time')
    plt.xlim(year_range)
    plt.xlabel('Year')
    plt.ylabel('Proportion')
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    st.pyplot(fig1)

    # Additional Graph: Bar chart for male vs. female counts
    st.subheader(f'Male vs. Female Counts for "{name_of_interest}"')
    if not filtered_data.empty:
        gender_counts = filtered_data.groupby(['year', 'sex'])['count'].sum().reset_index()
        sns.barplot(data=gender_counts, x='year', y='count', hue='sex')
        plt.title(f'Gender Distribution for "{name_of_interest}"')
        plt.xticks(rotation=90)
        plt.tight_layout()
        st.pyplot()
    else:
        st.warning('No data to display!')

with tab2:
    st.header("Data Summaries")

    # Text Output: Summary of most popular year
    if not filtered_data.empty:
        most_popular_year = filtered_data.loc[filtered_data['count'].idxmax()]['year']
        st.subheader(f'Most Popular Year for "{name_of_interest}"')
        st.write(f"The name '{name_of_interest}' was most popular in {most_popular_year}.")
    else:
        st.warning("No data available for the selected filters.")

    # Table: Display filtered data
    st.subheader("Filtered Data Table")
    st.write(filtered_data[['year', 'sex', 'count', 'prop']])

# Add an expander for app details
with st.expander("About This App"):
    st.write("""
        This app allows users to explore the popularity of baby names over time using data from the Social Security Administration. 
        Use the sidebar to filter by name, gender, and year range, and explore trends with dynamic graphs and data summaries.
    """)
