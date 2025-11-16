import streamlit as st
import json
import pandas as pd
import math
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re


# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Tesco data dashboard',
    page_icon='🛒', # This is an emoji shortcode. Could be a URL too.
)



# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_tesco_data(file):
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    #DATA_FILENAME = Path(__file__).parent/'data/tesco.json'
    
    data = json.load(file) 
   

    purchases = data["purchases"]
    orderedItems = []
    
    for visit in purchases:
        for item in visit["items"]:
            orderedItem = item
            orderedItem["timeStamp"] = visit["timestamp"]
            orderedItems.append(orderedItem)

    
    df = pd.DataFrame(orderedItems)
    df = df.query("name != 'Delivery Service Charge'")
    df = df.query("name != '4.00 Minimum Basket Charge Tesco.Com Groceries'")
    df = df.query("name != '2.50 SERVICE     CHARGE '")
    df = df.query("name != 'HOME DELIVERY    SUBSTITUTION     REFUND          '")
    df = df.query("name != '3.00 SERVICE     CHARGE '")
    df['timeStamp'] = pd.to_datetime(df['timeStamp'])
    df['Year'] = df['timeStamp'].dt.year
    df['year_month'] = df['timeStamp'].dt.to_period('M')
    
    
    
    full_df = pd.DataFrame(purchases)
    full_df['timestamp'] = pd.to_datetime(full_df['timestamp'])
    full_df['Year'] = full_df['timestamp'].dt.year
    full_df['year_month'] = full_df['timestamp'].dt.to_period('M')
    
    return df, full_df

#tesco_df, full_df = get_tesco_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# 🛒 Tesco data dashboard
See insights into your purchasing trends extracted from your tesco clubcard data

Visit this link [Tesco Data Website
](https://www.tesco.com/account/data-portability/en-GB/?srsltid=AfmBOorO2jQshWwglKpj2a1HoQyl3GMKA0MC5W1Zaa9IZ-TGE4IE42M8) to download your data, this process can take 24 hours

Once complete extract the Json file from inside the zip they provide you. Or you can use this example data
'''
with open("data/tesco.json", "rb") as file:
        st.download_button(
            label="Download example file",
            data=file,
            file_name="data/tesco.json"
        )
# Add some spacing
''
''


file = st.file_uploader("Choose a file", type="json")



if file is not None:
    tesco_df, full_df = get_tesco_data(file)    

    min_value = full_df['Year'].min()
    max_value = full_df['Year'].max()

    from_year, to_year = st.slider(
        'Which years are you interested in?',
        min_value=min_value,
        max_value=max_value,
        value=[min_value, max_value])


    ''
    ''
    ''

    # Filter the data
    filtered_tesco_df = full_df[
        (full_df['Year'] <= to_year)
        & (from_year <= full_df['Year'])
    ]

    yearly_metrics = (
        full_df.groupby('Year')
            .agg(
                # Metric 1: Average Order Value (Mean Basket Value)
                aov=('basketValueGross', 'mean'),
                
                # Metric 2: Average Items Per Order (Mean Number of Items)
                aipo=('numberOfItems', 'mean'),
                
                # Helper for Metric 3: Total Gross Value
                total_gross_value=('basketValueGross', 'sum'),
                
                # Helper for Metric 3: Total Number of Items
                total_items=('numberOfItems', 'sum'),
                
                # Optional: Count of visits
                total_visits=('timestamp', 'count')

            )
            .reset_index()
        )

    yearly_metrics['AIP'] = yearly_metrics['total_gross_value'] / yearly_metrics['total_items']

    yearly_metrics = yearly_metrics.rename(columns={
            'aov': 'Average Order Value (AOV)',
            'aipo': 'Average Items per Order (AIPO)',
            'AIP': 'Average Item Price (AIP)',
            'total_visits': 'Total Visits'
        })


    metric_options = [
            'Average Order Value (AOV)',
            'Average Items per Order (AIPO)',
            'Average Item Price (AIP)',
            'Total Visits'
        ]
        
    selected_metric = st.selectbox(
            "Select a Metric to Visualize:",
            options=metric_options
        )

        # Line Chart Visualization
    st.line_chart(
            yearly_metrics,
            x='Year',
            y=selected_metric,
            color="#0066FF", # Tesco-inspired blue
        )

    ''
    ''




    st.header(f'Most purchased item per year', divider='gray')

    ''
    options = sorted(full_df['Year'].unique())
    options.append("All Years")

    selection = st.segmented_control(
        "Directions", options, selection_mode="single"
    )


    if selection == 'All Years':
        # --- Logic for All Years ---
        
        # 1. Calculate Top 10 names across all years
        filtered_by_year_df = tesco_df

    else:
        # --- Logic for a Single Selected Year ---
        
        # 1. First, filter the main DataFrame by the selected year
        filtered_by_year_df = tesco_df[tesco_df['Year'] == selection]
        

    top_item_stats_df = (
            filtered_by_year_df.groupby('name')
            .agg(
                # Metric 1: Number of Times Bought (Frequency)
                times_bought=('name', 'count'),
                
                # Metric 2: Total Quantity of Items Bought
                total_quantity=('quantity', 'sum'),
                
                # Metric 3: Average Price of the Item
                average_price=('price', 'mean'),
                
                # Metric 4: Total Revenue from the Item
                total_spend=('price', 'sum')
            )
            .reset_index()
        )
        
        # 5. Clean up and rename the size column, and format data
    top_item_stats_df = top_item_stats_df.rename(columns={'times_bought': 'Times Bought (Orders)'})

        # 6. Sort by Times Bought (Frequency) descending
    top_item_stats_df = top_item_stats_df.sort_values(by='Times Bought (Orders)', ascending=False)
        
        # 7. Format the currency columns for display
    top_item_stats_df['Average Price'] = top_item_stats_df['average_price']
    top_item_stats_df['Total Spend'] = top_item_stats_df['total_spend']
    top_item_stats_df['Total Quantity'] = top_item_stats_df['total_quantity'].astype(int)
        
        # 8. Select and reorder final columns for display
    top_item_stats_df = top_item_stats_df[['name', 'Times Bought (Orders)', 'Total Quantity', 'Average Price', 'Total Spend']]


    st.dataframe(
        top_item_stats_df, 
        hide_index=True, 
        column_config={
            "name": st.column_config.TextColumn("Item Name"),
            "Average Price": st.column_config.NumberColumn(
                "Average Price",
                # This format string applies currency formatting, but the underlying data remains numeric for sorting
                format="£ %.2f" 
            ),
            "Total Spend": st.column_config.NumberColumn(
                "Total Spend",
                # This format string applies currency formatting, but the underlying data remains numeric for sorting
                format="£ %.2f",
            )
    }
)
else:
    print("none")
