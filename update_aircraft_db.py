#Developer Notes
#The download steps work, and a new database is created with a table containing all aircraft.
#The column headers are not created correctly.
#The step to filter for a specific aircraft type doesn't work.

import os
import requests
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
from contextlib import closing

# Constants
BASE_URL = "https://opensky-network.org/datasets/metadata/"
DB_FILENAME = "aircraftData.db"
TABLE_NAME = "Boeing747"
LOG_FILENAME = "download_log.txt"

def get_latest_csv_version(base_url):
    print("Fetching the latest dataset version...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all csv file links
            files = [a['href'] for a in soup.find_all('a', href=True) if 'aircraft-database-complete' in a['href'] and a['href'].endswith('.csv')]
            if files:
                latest_file = sorted(files)[-1]  # Gets the latest file
                print(f"Found latest version: {latest_file}")
                return latest_file
            else:
                print("No CSV files found on the page.")
                return None
        else:
            print("Failed to retrieve data from OpenSky Network.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def download_csv(url, filename):
    print(f"Downloading {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure download is successful
        with open(filename, 'wb') as f:
            f.write(response.content)
        print("Download completed.")
        return True
    except Exception as e:
        print(f"Failed to download the file: {e}")
        return False

def csv_to_sqlite(csv_file, db_file):
    table_name = "aircraft_type"
    print(f"Converting the entire CSV {csv_file} to SQLite with table {table_name}...")
    try:
        # Read CSV with header as the first row
        column_names = ["icao24","registration","manufacturericao","manufacturername","model","typecode","serialnumber","linenumber","icaoaircrafttype","operator","operatorcallsign","operatoricao","operatoriata","owner","testreg","registered","reguntil","status","built","firstflightdate","seatconfiguration","engines","modes","adsb","acars","notes","categoryDescription"]
        df = pd.read_csv(csv_file, encoding='ISO-8859-1', low_memory=False, header=0, names=column_names)
        
        # Delete all data from the table if it exists
        with closing(sqlite3.connect(db_file)) as conn:
            try:
                conn.execute(f"DELETE FROM {table_name}")
            except sqlite3.OperationalError:
                print(f"Table '{table_name}' does not exist. Skipping delete step.")
        
        # Insert CSV data into SQLite
        with closing(sqlite3.connect(db_file)) as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"SQLite database updated with {table_name} data.")
        return True
    except Exception as e:
        print(f"An error occurred while converting CSV to SQLite: {e}")
        return False
        
        # Insert CSV data into SQLite
        with closing(sqlite3.connect(db_file)) as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"SQLite database updated with {table_name} data.")
        return True
    except Exception as e:
        print(f"An error occurred while converting CSV to SQLite: {e}")
        return False

def filter_aircraft_type(db_file, source_table, aircraft_type):
    print(f"Filtering for {aircraft_type} aircraft...")
    try:
        target_table = aircraft_type.lower() + "_list"  # Generate table name based on aircraft type
        
        with closing(sqlite3.connect(db_file)) as conn:
            # Read new data from source table based on aircraft type
            print("Reading data from source table...")
            new_df = pd.read_sql_query(f"SELECT * FROM {source_table} WHERE [Unnamed: 4] LIKE '%{aircraft_type}%'", conn)

            # Save the filtered data to a new table named after aircraft type
            print(f"Saving filtered {aircraft_type} aircraft data to table '{target_table}'...")
            new_df.to_sql(target_table, conn, if_exists='replace', index=False)
        
        print(f"Filtered {aircraft_type} aircraft data saved to table '{target_table}'.")
        return True
    except Exception as e:
        print(f"An error occurred while filtering {aircraft_type} data: {e}")
        return False

def main():
    latest_version = get_latest_csv_version(BASE_URL)
    if latest_version:
        latest_csv_url = BASE_URL + latest_version
        latest_csv_filename = latest_version.split('/')[-1]

        if os.path.exists(LOG_FILENAME):
            with open(LOG_FILENAME, 'r') as log_file:
                last_downloaded = log_file.readline().strip()
                if last_downloaded == latest_csv_filename:
                    print("Latest version already downloaded. Skipping...")
                    return
        if download_csv(latest_csv_url, latest_csv_filename):
            if csv_to_sqlite(latest_csv_filename, DB_FILENAME):  # Remove TABLE_NAME argument
                with open(LOG_FILENAME, 'w') as log_file:
                    log_file.write(latest_csv_filename)
                if os.path.exists(latest_csv_filename):
                    os.remove(latest_csv_filename)
                print("Cleanup complete.")
        else:
            print("Failed to download the latest version.")
    else:
        print("No new version available or failed to identify latest version.")

if __name__ == "__main__":
    main()
