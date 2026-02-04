import os
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

# Versuche .env zu laden
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv nicht installiert
    pass

def fetch_front_articles():
    """
    Holt die Artikel vom Tagesanzeiger Front-Feed und gibt sie sortiert zurück.
    """
    feed_url = "https://feed-prod.unitycms.io/2/category/1"
    
    try:
        print(f"Hole Feed von {feed_url}...")
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extrahiere Artikel aus dem elements Array
        elements = data.get('content', {}).get('elements', [])
        
        # Filtere nur Artikel und Ticker
        articles = [
            elem for elem in elements 
            if elem.get('type') in ['articles', 'tickers']
        ]
        
        # Sortiere nach sortID
        articles.sort(key=lambda x: x.get('sortID', 999))
        
        print(f"✓ {len(articles)} Artikel gefunden")
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Fehler beim Abrufen des Feeds: {e}")
        return None
    except Exception as e:
        print(f"✗ Unerwarteter Fehler: {e}")
        return None

def format_email_body(articles):
    """
    Erstellt den Plain-Text Body für die E-Mail.
    """
    swiss_time = datetime.now(ZoneInfo("Europe/Zurich"))
    now = swiss_time.strftime("%d.%m.%Y, %H:%M Uhr")
    
    body = f"Tagesanzeiger Front - {now}\n"
    body += "=" * 60 + "\n\n"
    
    for index, article in enumerate(articles, start=1):
        title = article.get('content', {}).get('title', 'Kein Titel')
        url_path = article.get('content', {}).get('url', '')
        full_url = f"https://www.tagesanzeiger.ch{url_path}"
        
        body += f"Position {index}\n"
        body += f"Titel: {title}\n"
        body += f"URL: {full_url}\n\n"
    
    body += "=" * 60 + "\n"
    body += f"Insgesamt {len(articles)} Artikel auf der Front"
    
    return body

def send_email(body):
    """
    Versendet die E-Mail via Gmail SMTP.
    """
    # Hole Credentials aus Umgebungsvariablen
    sender_email = os.getenv('EMAIL_USER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipients = [
        "pascal.vanz@tamedia.ch", 
        "vanessa.hann@tamedia.ch",
        "patrick.kuehnis@tamedia.ch",
        "amir.mustedanagic@tamedia.ch",
        "tina.huber@tamedia.ch",
        "anna.baumgartner@tamedia.ch",
        "noah.fend@tamedia.ch",
        "matthias.chapman@tamedia.ch"]
    recipient_email = ", ".join(recipients)
    
    # Validierung
    if not sender_email or not sender_password:
        print("✗ Fehler: EMAIL_USER und EMAIL_PASSWORD müssen gesetzt sein!")
        print("  Erstelle eine .env Datei mit diesen Variablen.")
        return False
    
    # E-Mail erstellen
    swiss_time = datetime.now(ZoneInfo("Europe/Zurich"))
    subject = f"Tagesanzeiger Front-Artikel - {swiss_time.strftime('%d.%m.%Y')}"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # E-Mail versenden
    try:
        print(f"Sende E-Mail an {recipient_email}...")
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print("✓ E-Mail erfolgreich versendet!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("✗ Fehler: Authentifizierung fehlgeschlagen!")
        print("  Stelle sicher, dass du ein Gmail App-Passwort verwendest.")
        return False
    except Exception as e:
        print(f"✗ Fehler beim E-Mail-Versand: {e}")
        return False

def main():
    """
    Hauptfunktion: Orchestriert den gesamten Prozess.
    """
    print("\n" + "=" * 60)
    print("Tagesanzeiger Front-Artikel Scraper")
    print("=" * 60 + "\n")
    
    # 1. Artikel holen
    articles = fetch_front_articles()
    
    if not articles:
        print("\n✗ Abbruch: Keine Artikel gefunden")
        return
    
    # 2. E-Mail Body erstellen
    email_body = format_email_body(articles)
    
    # Optional: Body in Konsole ausgeben
    print("\n--- E-Mail Vorschau ---")
    print(email_body[:500] + "..." if len(email_body) > 500 else email_body)
    print("--- Ende Vorschau ---\n")
    
    # 3. E-Mail versenden
    success = send_email(email_body)
    
    if success:
        print("\n✓ Prozess erfolgreich abgeschlossen!\n")
    else:
        print("\n✗ Prozess mit Fehlern beendet\n")

if __name__ == "__main__":
    main()
