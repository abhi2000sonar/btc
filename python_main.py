import requests
import psycopg2
import schedule
import time
from datetime import datetime, timedelta

# Database connection parameters
DB_NAME = "data_challenge"
DB_USER = "as12421"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"

# Connect to your PostgreSQL database
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
cur = conn.cursor()

def fetch_btc_data():
    """Fetches BTC OHLC data from the CoinGecko API and stores it in PostgreSQL."""
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1"
    response = requests.get(url)
    data = response.json()
    
    for entry in data:
        timestamp, open_price, high, low, close = entry
        try:
            cur.execute("INSERT INTO btc_ohlc (timestamp, open, high, low, close) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (timestamp) DO NOTHING;",
                        (datetime.fromtimestamp(timestamp / 1000), open_price, high, low, close))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            conn.rollback()

def check_price_alert():
    """Checks for significant price changes and generates alerts."""
    try:
        cur.execute("SELECT AVG(close) FROM btc_ohlc WHERE timestamp > NOW() - INTERVAL '5 minutes';")
        avg_price_last_5min = cur.fetchone()[0]
        cur.execute("SELECT close FROM btc_ohlc ORDER BY timestamp DESC LIMIT 1;")
        current_price = cur.fetchone()[0]

        if avg_price_last_5min is not None and current_price is not None:
            change_percent = (current_price - avg_price_last_5min) / avg_price_last_5min * 100
            if abs(change_percent) > 2:
                print(f"Alert: BTC price change is {change_percent:.2f}% in the last 5 minutes.")
    except psycopg2.Error as e:
        print(f"Database error: {e}")

# Schedule the BTC data fetch to run every second
schedule.every(1).seconds.do(fetch_btc_data)

# Schedule the price alert check to run every minute
schedule.every(1).minutes.do(check_price_alert)

while True:
    schedule.run_pending()
    time.sleep(1)