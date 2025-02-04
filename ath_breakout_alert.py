# %%
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import os
from email.message import EmailMessage
import ssl
import smtplib
import datetime
# Function to scrape the Nifty 500 stocks data from Wikipedia and find the all-time high stocks
def nifty_500_ath():
    """
    Scrapes the list of Nifty 500 stocks from Wikipedia, retrieves historical stock data
    using the Yahoo Finance API, and identifies stocks currently at their all-time high.

    Returns:
        pd.DataFrame: DataFrame containing the details of stocks at all-time highs.
        list: List of tickers for which data could not be downloaded.
    """
    # URL of the Wikipedia page containing Nifty 500 stocks information
    url = "https://en.wikipedia.org/wiki/NIFTY_500"

    # Sending an HTTP GET request to fetch the webpage content
    response = requests.get(url)

    # Parsing the HTML content of the page
    soup = BeautifulSoup(response.content, "html.parser")

    # Locate the table containing the Nifty 500 stock data
    table = soup.find("table", {"class": "wikitable sortable mw-collapsible"})

    # Extracting the data from the table
    data = []
    if table:
        rows = table.find_all("tr")
        headers = [header.text.strip() for header in rows[0].find_all("td")]

        # Extract data row by row
        for row in rows[1:]:
            cells = row.find_all("td")
            if cells:
                data.append([cell.text.strip() for cell in cells])

        # Creating a DataFrame from the extracted data
        nifty_500_df = pd.DataFrame(data, columns=headers)
        nifty_500_df.rename(columns={"Symbol": "Ticker", "Company  Name": "Company Name", "ISIN  Code": "ISIN Code"}, inplace=True)
        
        # Append '.NS' to all tickers to indicate NSE tickers for Yahoo Finance API
        nifty_500_ticker = nifty_500_df['Ticker'].str.cat([".NS"] * len(nifty_500_df['Ticker']))
        print("Data scraped successfully.")
    else:
        print("Could not find the table on the page.")

    # Function to find the all-time high stocks
    def ath_stock_finder(ticker):
        """
        Identifies if the stock is currently at its all-time high.

        Args:
            ticker (str): Ticker symbol of the stock.

        Returns:
            tuple: Ticker symbol, current price, and previous all-time high if the stock is at ATH.
            None: If the stock is not at ATH.
        """
        # Fetch monthly adjusted data for the ticker
        df = yf.download(ticker, interval='1mo', back_adjust=True, progress=False)[['Close', 'High']]
        df['Date'] = df.index
        df['Date'] = pd.to_datetime(df['Date'])
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df.index = df['Date']
        df = df.drop('Date', axis=1)
        df.columns = [''] * len(df.columns)
        df.columns = ['Close', 'High']
        
        # Calculate previous ATH and current price
        previous_ath = df['High'].shift(1).max()
        current_price = df['Close'].iloc[-1]
        ticker_name = ticker.replace('.NS', '')
        
        # Check if current price exceeds previous ATH
        if current_price > previous_ath:
            return ticker_name, current_price, previous_ath
        else:
            return None

    # Identify all-time high stocks
    ath_stocks_list = []
    failed_tickers = []
    for ticker in nifty_500_ticker:
        try:
            ath_stock_result = ath_stock_finder(ticker)
            if ath_stock_result:
                ath_stocks_list.append(ath_stock_result)
        except:
            # Track tickers for which data download failed
            failed_tickers.append(ticker.replace('.NS', ''))
            pass

    # Create a DataFrame for all-time high stocks
    ath_stocks = pd.DataFrame(ath_stocks_list, columns=['Ticker', 'Current Price', 'Previous ATH'])

    # Join with the original Nifty 500 data to enrich the details
    ath_stocks = ath_stocks.join(nifty_500_df.set_index('Ticker'), on='Ticker')
    ath_stocks.drop(['Sl.No', 'Series', 'ISIN Code'], axis=1, inplace=True)
    ath_stocks['Current Price'] = ath_stocks['Current Price'].astype(float).round(2)
    ath_stocks['Previous ATH'] = ath_stocks['Previous ATH'].astype(float).round(2)
    ath_stocks = ath_stocks[['Company Name', 'Ticker', 'Industry', 'Current Price', 'Previous ATH']]

    return ath_stocks, failed_tickers

def send_email(sender_email, sender_password, recipient, subject, df, failed_tickers):
    """
    Sends an email containing the list of all-time high stocks in HTML format.

    Args:
        sender_email (str): Email address of the sender.
        sender_password (str): Password for the sender email.
        recipient (str): Email address of the recipient.
        subject (str): Subject line of the email.
        df (pd.DataFrame): DataFrame containing the stocks at all-time highs.
        failed_tickers (list): List of tickers for which data download failed.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient

    # Convert DataFrame to HTML table
    html_table = df.to_html(index=False, justify='center')

    # Add the custom message above the table
    email_body = f"<p>List of All Time High Stocks. Keep Growing!!🚀🚀</p>{html_table}"

    # Add failed tickers to the email
    if failed_tickers:
        failed_tickers_str = ', '.join(failed_tickers)
        email_body += f"<p>Failed to download data for the following tickers: {failed_tickers_str}</p>"

    # Attach the email body as an HTML alternative
    msg.add_alternative(email_body, subtype='html')

    # Connect to the SMTP server and send the email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
    print("Email sent successfully.")

def main():
    """
    Main function to execute the script:
    1. Scrape Nifty 500 stock data.
    2. Identify all-time high stocks.
    3. Send an email with the results.
    """
    month = datetime.datetime.now().strftime("%B %Y")
    subject = f"Nifty 500 All-Time High Stocks - {month}"
    df, failed_tickers = nifty_500_ath()

    # Read email credentials and recipient information from local files
    email_path = os.path.join(os.getcwd(), 'EMAIL_SENDER.txt')
    password_path = os.path.join(os.getcwd(), 'EMAIL_PASSWORD.txt')
    recipient_path = os.path.join(os.getcwd(), 'RECIPIENT.txt')
    sender_email = open(email_path, 'r').read()
    sender_password = open(password_path, 'r').read()
    recipient = open(recipient_path, 'r').read()

    # Send the email
    send_email(sender_email, sender_password, recipient, subject, df, failed_tickers)

if __name__ == "__main__":
    main()


# %%



