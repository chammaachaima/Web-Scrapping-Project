import pandas as pd
import os
import glob

# Set your folder path
folder_path =r"C:\Users\Dell\OneDrive - Ministere de l'Enseignement Superieur et de la Recherche Scientifique\Bureau\CSR files sec project"  # Change this to your folder path
output_folder = os.path.join(folder_path, "cleaned")
os.makedirs(output_folder, exist_ok=True)

# Loop through all CSV files in the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

for file_path in csv_files:
    try:
        # Load data
        df = pd.read_csv(file_path)

        # Drop rows with missing essential data
        df = df.dropna(subset=['Content', 'Date'])

        # Convert Date to datetime format
        df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y", errors='coerce')
        df = df.dropna(subset=['Date'])  # Drop rows with invalid dates

        # Fill missing values
        df['Title'] = df['Title'].fillna("No Title")
        df['Brand Response'] = df['Brand Response'].fillna("No response")

        # Create Year-Month column
        df['YearMonth'] = df['Date'].dt.to_period('M')

        # Extract Country
        df['Country'] = df['Reviewer'].str.extract(r',\s*(\w+)$')

        # Reset index
        df = df.reset_index(drop=True)

        # Save cleaned file
        filename = os.path.basename(file_path)
        cleaned_path = os.path.join(output_folder, f"cleaned_{filename}")
        df.to_csv(cleaned_path, index=False)

        print(f"✅ Cleaned: {filename}")

    except Exception as e:
        print(f"❌ Error with {file_path}: {e}")
