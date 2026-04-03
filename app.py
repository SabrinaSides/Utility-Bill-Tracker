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

    # Check for accounts with potentially missing instances
    if 'Num' in filtered_df.columns and 'Date' in filtered_df.columns:
        # Extract base account number (remove patterns like " Jan25", " fee", "-fee" at the end)
        import re
        base_accounts = filtered_df['Num'].astype(str).str.replace(r'(\s[A-Za-z]{3}\d{2}$|[-\s][Ff]ee$)', '', regex=True)
        
        # Extract month-year from Date column
        filtered_df['Month'] = pd.to_datetime(filtered_df['Date']).dt.to_period('M')
        
        # Create a temporary dataframe with base accounts
        temp_df = filtered_df.copy()
        temp_df['Base_Account'] = base_accounts
        
        # Get all unique months sorted
        all_months = sorted(temp_df['Month'].unique())
        
        # Find accounts missing in months after their first appearance
        missing_accounts = []
        
        for account in temp_df['Base_Account'].unique():
            account_data = temp_df[temp_df['Base_Account'] == account]
            account_months = set(account_data['Month'])
            
            # Find first month this account appears
            first_month = min(account_months)
            
            # Expected months: from first appearance to end of dataset
            expected_months = [m for m in all_months if m >= first_month]
            
            # Find missing months
            missing_months = [m for m in expected_months if m not in account_months]
            
            # Only include if missing 3 or fewer consecutive months
            if missing_months and len(missing_months) <= 3:
                # Check if they are consecutive
                consecutive_count = 1
                max_consecutive = 1
                for i in range(1, len(missing_months)):
                    if (missing_months[i] - missing_months[i-1]).n == 1:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 1
                
                    if max_consecutive <= 3:
                        # Check if account is already in the list to avoid duplicates
                        if not any(acc == account for acc, _ in missing_accounts):
                            missing_accounts.append((account, missing_months))
        
        # Store missing accounts in session state
        if 'excluded_accounts' not in st.session_state:
            st.session_state.excluded_accounts = set()
        
        # Filter out excluded accounts
        filtered_missing = [(acc, months) for acc, months in missing_accounts if acc not in st.session_state.excluded_accounts]
        
        if len(filtered_missing) > 0:
            st.write(f"**Accounts that might be missing bills:**")
            for account_num, missing_months in filtered_missing:
                col1, col2 = st.columns([0.5, 9.5])
                with col1:
                    if st.button("❌", key=f"remove_{account_num}"):
                        st.session_state.excluded_accounts.add(account_num)
                        st.rerun()
                with col2:
                    month_list = ", ".join([m.strftime('%m/%Y') for m in missing_months])
                    st.write(f"{account_num}: {month_list}")
        else:
            st.success("✓ No accounts missing bills")
        
        st.write("---")
        
        # Clean up temporary column
        filtered_df = filtered_df.drop('Month', axis=1)

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