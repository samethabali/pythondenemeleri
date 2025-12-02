import requests
import smtplib
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

load_dotenv()

sender = os.getenv("MAIL_SENDER")
receiver = os.getenv("MAIL_RECEIVER")
password = os.getenv("MAIL_APP_PASSWORD")

url = 'https://www.amazon.com.tr/Philips-Arada-Erkek-Bak%C4%B1m-Seti/dp/B0CJYJ45TS'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

def check_price():
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find(id='productTitle').getText().strip()
    title=title[76:]
    print(title)
    content = (
        soup.find('span', class_='a-offscreen') or
        soup.find('span', class_='a-price-whole')
    )
    content = content.get_text().strip()
    content=content.replace('TL', '').replace('₺', '').replace('.', '').replace(',', '.').strip()
    price=float(content)
    print(price)
    if price<2500:
        send_mail(title)
    

def send_mail(title):
    try:
        server=smtplib.SMTP('smtp.gmail.com',587)
        server.ehlo()
        server.starttls()
        server.login(sender,password)
        subject= title +'istedigin fiyata dustu'
        body='bu linkten gidebilirsin -->  '+url
        mailcontent=f"To:{receiver}\nFrom:{sender}\nSubject:{subject}\n\n{body}"
        server.sendmail(sender,receiver,mailcontent)
        print('mail gonderildi')
    except smtplib.SMTPException as e:
        print(e)
    finally:
        server.quit()


while(1):
    check_price()
    time.sleep(60*60)