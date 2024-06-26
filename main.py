import functions_framework
import pandas as pd
from google.cloud import bigquery
import datetime
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@functions_framework.http
def update_data_v2(request):
    logging.info("Starting data update process")

    client = bigquery.Client()
    logging.debug("BigQuery client initialized")

    # Fetch data from CoinGecko API
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    logging.debug(f"API response status: {response.status_code}")
    data = response.json()
    logging.debug(f"Data fetched: {len(data)} items")

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    logging.debug("Data converted to DataFrame")

    # Ensure all necessary columns are present and specify data types
    required_columns = {
        "symbol": str, "name": str, "current_price": float, "market_cap": int, 
        "market_cap_rank": int, "fully_diluted_valuation": float, "total_volume": float, "high_24h": float, 
        "low_24h": float, "price_change_24h": float, "price_change_percentage_24h": float, 
        "market_cap_change_24h": float, "market_cap_change_percentage_24h": float, "circulating_supply": float, 
        "total_supply": float, "max_supply": float, "ath": float, "ath_change_percentage": float, 
        "ath_date": str, "atl": float, "atl_change_percentage": float, "atl_date": str, "timestamp": 'datetime64[ns]'
    }

    # Add missing columns with default values
    for column, dtype in required_columns.items():
        if column in df:
            df[column] = df[column].astype(dtype)
        else:
            df[column] = None

    # Ensure the 'timestamp' field is set to the current time
    df['timestamp'] = pd.to_datetime(datetime.datetime.utcnow())

    # Define table IDs
    table_id_cleaned = "battle-of-jericho.sheets_data.coingecko_data_cleaned_new"
    table_id = "battle-of-jericho.sheets_data.coingecko_data_new"
    table_id_with_factors = "battle-of-jericho.sheets_data.coingecko_data_with_factors_new"

    # Configure the load job
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    # Load data into BigQuery tables
    try:
        logging.info(f"Loading data into {table_id_cleaned}")
        job_cleaned = client.load_table_from_dataframe(df, table_id_cleaned, job_config=job_config)
        job_cleaned.result()
        logging.info("Data successfully loaded into coingecko_data_cleaned_new")

        logging.info(f"Loading data into {table_id}")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logging.info("Data successfully loaded into coingecko_data_new")

        logging.info(f"Loading data into {table_id_with_factors}")
        job_with_factors = client.load_table_from_dataframe(df, table_id_with_factors, job_config=job_config)
        job_with_factors.result()
        logging.info("Data successfully loaded into coingecko_data_with_factors_new")
    except Exception as e:
        logging.error(f"Error loading data into BigQuery: {e}")

    return "Data uploaded successfully"
