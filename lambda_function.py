import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import os
from email.message import EmailMessage
import ssl
import smtplib
import datetime
import json


def ath_stock_finder(ticker):
    """
    Identifies if a stock is currently at its all-time high.

    Args:
        ticker (str): NSE ticker symbol with '.NS' suffix (e.g., 'RELIANCE.NS').

    Returns:
        tuple: (ticker_name, current_price, previous_ath) if the stock is at ATH.
        None: If the stock is not at ATH.
    """
    # Fetch full monthly adjusted OHLCV data for the ticker
    df = yf.download(
        ticker,
        interval='1mo',
        period="max",
        back_adjust=True,
        progress=False,
        auto_adjust=True
    )[['Close', 'High']]

    # Normalize the index to string dates
    df['Date'] = pd.to_datetime(df.index).strftime('%Y-%m-%d')
    df.index = df['Date']
    df = df.drop('Date', axis=1)
    df.columns = ['Close', 'High']

    # Previous ATH = max High across all months before the current month
    previous_ath = df['High'].shift(1).max()
    current_price = df['Close'].iloc[-1]
    ticker_name = ticker.replace('.NS', '')

    # A breakout is confirmed when current price exceeds the previous all-time high
    if current_price > previous_ath:
        return ticker_name, current_price, previous_ath
    return None


def nifty_500_ath():
    """
    Scrapes the NIFTY 500 stock list from Wikipedia, downloads historical price data
    via the Yahoo Finance API, and identifies stocks currently at their all-time high.

    Returns:
        pd.DataFrame: Enriched DataFrame of ATH breakout stocks with company name,
                      ticker, industry, current price, and previous ATH.
        list: Tickers for which data could not be downloaded.
    """
    url = "https://en.wikipedia.org/wiki/NIFTY_500"
    headers = {"User-Agent": "CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Locate the NIFTY 500 constituents table
    table = soup.find("table", {"class": "wikitable sortable mw-collapsible"})

    if not table:
        print("Could not find the NIFTY 500 table on the Wikipedia page.")
        return pd.DataFrame(), []

    rows = table.find_all("tr")
    col_headers = [header.text.strip() for header in rows[0].find_all("td")]

    data = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if cells:
            data.append([cell.text.strip() for cell in cells])

    nifty_500_df = pd.DataFrame(data, columns=col_headers)
    nifty_500_df.rename(
        columns={
            "Symbol": "Ticker",
            "Company  Name": "Company Name",
            "ISIN  Code": "ISIN Code"
        },
        inplace=True
    )
    print(f"Scraped {len(nifty_500_df)} tickers from Wikipedia.")

    # Append '.NS' suffix for Yahoo Finance NSE tickers
    nifty_500_tickers = nifty_500_df['Ticker'] + '.NS'

    # Scan each ticker for ATH breakout
    ath_stocks_list = []
    failed_tickers = []

    for ticker in nifty_500_tickers:
        try:
            result = ath_stock_finder(ticker)
            if result:
                ath_stocks_list.append(result)
        except Exception as e:
            failed_tickers.append(ticker.replace('.NS', ''))
            print(f"Failed to fetch data for {ticker}: {e}")

    print(f"Scan complete. {len(ath_stocks_list)} ATH breakouts found. {len(failed_tickers)} tickers failed.")

    # Build and enrich the ATH results DataFrame
    ath_stocks = pd.DataFrame(ath_stocks_list, columns=['Ticker', 'Current Price', 'Previous ATH'])
    ath_stocks = ath_stocks.join(nifty_500_df.set_index('Ticker'), on='Ticker')
    ath_stocks.drop(['Sl.No', 'Series', 'ISIN Code'], axis=1, inplace=True)
    ath_stocks['Current Price'] = ath_stocks['Current Price'].astype(float).round(2)
    ath_stocks['Previous ATH'] = ath_stocks['Previous ATH'].astype(float).round(2)
    ath_stocks = ath_stocks[['Company Name', 'Ticker', 'Industry', 'Current Price', 'Previous ATH']]

    return ath_stocks, failed_tickers


def send_email(sender_email, sender_password, recipient, subject, df, failed_tickers):
    """
    Sends an HTML-formatted email containing the ATH breakout stock list.

    Args:
        sender_email (str): Gmail address used as the sender.
        sender_password (str): Gmail App Password (not the account login password).
        recipient (str): Recipient email address.
        subject (str): Email subject line.
        df (pd.DataFrame): DataFrame of ATH breakout stocks.
        failed_tickers (list): Tickers for which data download failed.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    html_table = df.to_html(index=False, justify='center')
    email_body = f"<p>List of All Time High Stocks. Keep Growing!! 🚀🚀</p>{html_table}"

    if failed_tickers:
        failed_tickers_str = ', '.join(failed_tickers)
        email_body += f"<p><em>Note: Data could not be retrieved for the following tickers: {failed_tickers_str}</em></p>"

    msg.add_alternative(email_body, subtype='html')

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print("Email sent successfully.")


def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Execution flow:
        1. Load credentials from Lambda environment variables.
        2. Scrape NIFTY 500 stock list from Wikipedia.
        3. Identify stocks at all-time highs.
        4. Send a formatted HTML email alert to the configured recipient.

    Environment Variables:
        EMAIL_SENDER    -- Gmail address used to send alerts.
        EMAIL_PASSWORD  -- Gmail App Password for SMTP authentication.
        RECIPIENT       -- Email address to receive the alert.

    Returns:
        dict: HTTP-style response with statusCode and body.
    """
    # Load credentials from Lambda environment variables — never hardcoded or stored in files
    sender_email = os.environ['EMAIL_SENDER']
    sender_password = os.environ['EMAIL_PASSWORD']
    recipient = os.environ['RECIPIENT']

    month = datetime.datetime.now().strftime("%B %Y")
    subject = f"Nifty 500 All-Time High Breakout Stocks — {month}"

    df, failed_tickers = nifty_500_ath()
    send_email(sender_email, sender_password, recipient, subject, df, failed_tickers)

    return {
        'statusCode': 200,
        'body': json.dumps(f"Email sent successfully to {recipient}")
    }
