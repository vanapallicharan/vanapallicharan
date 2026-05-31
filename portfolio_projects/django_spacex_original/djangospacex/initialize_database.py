import sqlite3
import pandas as pd

def initialize_database(excel_path):
    try:
        # Read data from Excel file
        df = pd.read_excel(excel_path)

        # Normalize column names by stripping whitespace
        df.columns = df.columns.str.strip()

        # Debug print statement for found columns
        print(f"Found columns: {df.columns}")

        # Map actual columns to the expected names
        column_mapping = {
            'S.NO': 'S. NO',
            'Products': 'Products',
            'OEM': 'OEM',
            'Price': 'Price'
        }

        # Select and rename the relevant columns
        df = df[list(column_mapping.keys())].rename(columns=column_mapping)

        # Check if required columns are present
        required_columns = set(column_mapping.values())
        actual_columns = set(df.columns)

        missing_columns = required_columns - actual_columns
        if missing_columns:
            raise ValueError(f"The Excel file is missing the following columns: {missing_columns}")

        # Convert DataFrame columns to appropriate types
        df['S. NO'] = pd.to_numeric(df['S. NO'], errors='coerce').dropna().astype(int)
        df['Products'] = df['Products'].astype(str)
        df['OEM'] = pd.to_numeric(df['OEM'], errors='coerce').dropna().astype(float)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').dropna().astype(float)

        # Connect to SQLite database
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()

        # Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            S_NO INTEGER PRIMARY KEY,
            Description TEXT,
            Price REAL
        )
        ''')

        # Insert data into the table
        cursor.executemany('''
        INSERT OR REPLACE INTO Products (S_NO, Description, Price)
        VALUES (?, ?, ?)
        ''', df[['S. NO', 'Products', 'OEM']].values.tolist())

        conn.commit()
        print("Database initialized and populated with data from Excel.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    excel_path = input("Enter the path to the Excel file (e.g., C:\\Users\\chara\\djangospacex\\data.xlsx): ")
    try:
        initialize_database(excel_path)
    except Exception as e:
        print(f"An error occurred: {e}")
