# ATH-Breakout-Stocks
A Python project that identifies all-time high breakout stocks and emails them at the end of every month. Built using AWS Lambda, EventBridge, S3, and CloudWatch.

## 📌 Project Overview
This Python-based project automatically identifies **all-time high (ATH) breakout stocks** from the **NIFTY 500** index and sends an email alert at the end of each month. The project is fully automated using **AWS Lambda, EventBridge, S3, and CloudWatch**.

## 🚀 Features
- **Scrapes** NIFTY 500 ticker list from Wikipedia using `requests` and `BeautifulSoup`.
- **Downloads** stock prices via `yfinance`.
- **Cleans** the data using `pandas`.
- **Filters** breakout stocks and creates a DataFrame.
- **Sends email alerts** using `smtplib`, `SSL`, and Python's `email` library.
- **Automates execution** via **AWS Lambda & EventBridge**.
- **Stores dependencies** in **AWS S3** and logs executions in **AWS CloudWatch**.

## 🛠️ Technologies Used
- **Python** (pandas, requests, BeautifulSoup, yfinance, smtplib)
- **AWS Lambda** (for serverless execution)
- **AWS EventBridge** (for scheduling)
- **AWS S3** (for storing dependencies)
- **AWS CloudWatch** (for logging)

## 👥 User Configuration
To use this project, users must create three text files containing email credentials:
- `EMAIL_PASSWORD.txt` (contains sender's email password)
- `EMAIL_SENDER.txt` (contains sender's email address)
- `RECIPIENT.txt` (contains recipient's email address)

## 🔍 How It Works
1. The script scrapes the latest **NIFTY 500 stock symbols** from Wikipedia.
2. It downloads **historical stock prices** using the `yfinance` library.
3. A filtering mechanism **identifies breakout stocks** (stocks hitting all-time highs).
4. The identified stocks are formatted into an **email report**.
5. The report is sent to a **pre-configured email**.
6. The script is scheduled via **AWS Lambda & EventBridge** to run at the **end of each month**.

## 📧 Contact
If you have any questions or feedback, feel free to reach out!

📩 pateldhir97@gmail.com 
🔗 [LinkedIn Profile](https://www.linkedin.com/in/dhir-patel14/)  
📌 **GitHub**: [pateldhir97](https://github.com/pateldhir97/)
