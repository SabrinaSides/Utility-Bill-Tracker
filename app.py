import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Set the page layout to wide
st.set_page_config(layout="wide")

st.title("Utility Bill Tracker")

# Create a directory to save uploaded files
os.makedirs("data", exist_ok=True)

from datetime import datetime

# File uploader widget
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Read the Excel file into a DataFrame
    df = pd.read_excel(uploaded_file, header=4)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Filter out rows where the transaction type is "Bill Payment"
    if 'transaction type' in df.columns:
        filtered_df = df[df['transaction type'] != 'bill payment (check)']
    else:
        st.error("The column 'Transaction type' is not found in the uploaded file.")
        st.stop()
    
    # Select only the specified columns
    columns_to_display = ['date', 'num', 'name', 'a/p paid']
    filtered_df = filtered_df[[col for col in columns_to_display if col in df.columns]]

    # Capitalize the first letter of each column name
    filtered_df.columns = filtered_df.columns.str.title()

    # Replace missing or non-'Paid' values in 'A/P Paid' with 'Unpaid'
    if 'A/P Paid' in filtered_df.columns:
        filtered_df['A/P Paid'] = filtered_df['A/P Paid'].apply(lambda x: 'Paid' if str(x).strip().lower() == 'paid' else 'Unpaid')

    # Filter out rows without a 'Num' value
    if 'Num' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Num'].notna()]

     # Add search input for Num value
    search_num = st.text_input("Search by Num:", "")
    
    # Filter by search term if provided
    if search_num:
        filtered_df = filtered_df[filtered_df['Num'].astype(str).str.contains(search_num, case=False, na=False)]


    # Rearrange rows so that 'Unpaid' rows appear at the top
    filtered_df = filtered_df.sort_values(by='A/P Paid', ascending=False)

    # Automatically save the file with the current date
    current_date = datetime.now().strftime("%m-%d-%Y")
    file_path = f"data/{current_date}.csv"
    filtered_df.to_csv(file_path, index=False)
    st.success(f"Data automatically saved to {file_path}")

    # Define a function to color rows where 'A/P Paid' is 'Unpaid'
    def highlight_unpaid(row):
        if row['A/P Paid'] == 'Unpaid':
            return ['background-color: #f28b82'] * len(row)
        return [''] * len(row)

    # Apply the row highlighting
    styled_df = filtered_df.style.apply(highlight_unpaid, axis=1)

    # Display the styled DataFrame with a larger default size
    st.write("Filtered File Content:")
    st.dataframe(styled_df, use_container_width=True)