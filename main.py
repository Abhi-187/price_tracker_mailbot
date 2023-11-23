import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

def get_amazon_price(url):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}  # Set an appropriate user agent
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the price element based on the page structure
    price_element = soup.find('span', {'class': 'a-price-whole'})
    product_name_element = soup.find('span', {'id': 'productTitle'})
    
    if price_element:
        current_price = price_element.get_text().strip()
        product_name = product_name_element.get_text().strip()
        return current_price, product_name
    else:
        return None,None

def send_notification(to_email, product_url, current_price, previous_price, product_name):
    # Set up your email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'apnatracker187@gmail.com'
    sender_password = 'kmwnahmaqbysetf*' #create your own app password in the security menu of your Google account

    # Compose the email
    subject = 'Amazon Price Drop Alert!'
    
    # Additional information for the HTML-formatted email body
    product_info = f"<p><strong>Product URL:</strong> <a href='{product_url}'>{product_url}</a></p>"
    current_price_info = f"<p><strong>Current Price:</strong> {current_price}</p>"
    previous_price_info = f"<p><strong>Previous Price:</strong> {previous_price}</p>"
    product_name_info = f"<p><strong>Product Name:</strong> {product_name}</p>" if product_name else ""
    
    # Full HTML-formatted email body
    body = f"""
        <html>
            <body>
                <p>The price of your tracked product has dropped!</p>
                {product_info}
                {current_price_info}
                {previous_price_info}
                {product_name_info}
            </body>
        </html>
    """

    # Create a MIME multipart message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'html'))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        
def update_previous_price(product_url, current_price):
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            product_url TEXT PRIMARY KEY,
            previous_price REAL
        )
    ''')

    # Insert or update the current price
    cursor.execute('''
        INSERT OR REPLACE INTO prices (product_url, previous_price)
        VALUES (?, ?)
    ''', (product_url, float(current_price)))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def get_previous_price(product_url):
    # Connect to the SQLite database
    conn = sqlite3.connect('prices.db')
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            product_url TEXT PRIMARY KEY,
            previous_price REAL
        )
    ''')

    # Retrieve the previous price for the given product URL
    cursor.execute('''
        SELECT previous_price FROM prices
        WHERE product_url = ?
    ''', (product_url,))

    # Fetch the result
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    # Return the previous price if found, otherwise return a default value
    return result[0] if result else None

def check_price_and_notify(to_email, product_url):
    current_price, product_name = get_amazon_price(amazon_url)
    
    if current_price:
        # Retrieve previous price from the database
        previous_price = get_previous_price(product_url)

        # Compare prices
        if previous_price is None or float(current_price) < previous_price:
            # Send notification and update the database with the new price
            send_notification(to_email, product_url, current_price, previous_price,product_name)
            update_previous_price(product_url, current_price)
            print(f"Updated previous price to: {current_price}")
        else:
            print("No price drop detected.")
    else:
        print("Unable to retrieve the current price.")


# Example usage
amazon_url = "https://www.amazon.in/STRIFF-Adjustable-Patented-Ventilated-Compatible/dp/B07XCM6T4N/ref=sr_1_3?keywords=laptop+stand&qid=1687373405&sprefix=laptop+%2Caps%2C349&sr=8-3"
to_email = 'patel.abhi0187@gmail.com'

# Check the price and send notification if there's a drop
check_price_and_notify(to_email, amazon_url)


