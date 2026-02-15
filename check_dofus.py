import feedparser
import requests
import os
import io
import re
import html  # <--- Nouveau pour décoder les &eacute; etc.
from dotenv import load_dotenv

load_dotenv()

FEEDS = {
    "news": {
        "rss": "https://www.dofus.com/fr/rss/news.xml",
        "webhook": os.getenv('WEBHOOK_NEWS'),
        "file": "last_news.txt",
        "color": 3066993,
        "prefix": "📜 ACTU"
    },
    "devblog": {
        "rss": "https://www.dofus.com/fr/rss/devblog.xml",
        "webhook": os.getenv('WEBHOOK_DEVBLOG'),
        "file": "last_devblog.txt",
        "color": 15105570,
        "prefix": "🔨 DEVBLOG"
    },
    "changelog": {
        "rss": "https://www.dofus.com/fr/rss/changelog.xml",
        "webhook": os.getenv('WEBHOOK_CHANGELOG'),
        "file": "last_changelog.txt",
        "color": 15548997,
        "prefix": "🔄 MAJ"
    }
}

def clean_html(raw_html):
    """Supprime les balises HTML et décode les entités (accentuation)."""
    # 1. On décode les entités HTML (&eacute; -> é)
    decoded_text = html.unescape(raw_html)
    # 2. On supprime les balises HTML
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', decoded_text)
    # 3. On nettoie les espaces en trop et on limite la taille
    final_text = " ".join(cleantext.split())
    return final_text[:250] + "..." if len(final_text) > 250 else final_text

def check_feeds():
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    for category, data in FEEDS.items():
        print(f"Vérification de {category}...")
        
        if not data['webhook']:
            print(f"⚠️ Webhook {category} manquant")
            continue

        try:
            response = requests.get(data['rss'], headers=headers, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(io.BytesIO(response.content))
            
            if not feed.entries:
                continue

            latest = feed.entries[0]
            entry_id = latest.id
            entry_title = latest.title.strip()
            entry_link = latest.link.strip()
            
            description_raw = latest.summary if 'summary' in latest else ""
            entry_description = clean_html(description_raw)

            last_id = None
            if os.path.exists(data['file']):
                with open(data['file'], "r") as f:
                    last_id = f.read().strip()

            if entry_id != last_id:
                print(f"🆕 Nouveau : {entry_title}")
                
                payload = {
                    "embeds": [{
                        "author": {"name": data['prefix']},
                        "title": entry_title,
                        "url": entry_link,
                        "description": entry_description,
                        "color": data['color'],
                        "footer": {"text": "Dofus RSS Monitor"}
                    }]
                }
                
                res = requests.post(data['webhook'], json=payload)
                
                if res.status_code in [200, 204]:
                    with open(data['file'], "w") as f:
                        f.write(entry_id)
                    print(f"🚀 Envoyé !")
                else:
                    print(f"❌ Erreur : {res.status_code}")
            else:
                print(f"😴 Déjà connu.")

        except Exception as e:
            print(f"💥 Erreur sur {category}: {e}")

if __name__ == "__main__":
    check_feeds()