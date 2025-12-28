import requests
from bs4 import BeautifulSoup
import feedparser
import json
import datetime
from time import mktime

# --- ΛΙΣΤΑ ΣΤΟΧΩΝ (FULL AUTOMATED) ---
# Χρησιμοποιούμε RSS όπου υπάρχει (είναι πιο γρήγορο) και HTML scraping στα υπόλοιπα
SOURCES = [
    {
        "name": "Anemos 95.6 (Σάμος)",
        "type": "rss",
        "url": "https://anemos956.gr/feed/",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=498",
        "audience": "low", 
        "schedule": "09:00 - 12:00"
    },
    {
        "name": "Fly FM 89.7 (Σπάρτη)",
        "type": "rss",
        "url": "https://flynews.gr/feed/",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=792",
        "audience": "low",
        "schedule": "Πρωινή Ζώνη"
    },
    {
        "name": "Radio Polis 99.4 (Λάρισα)",
        "type": "rss",
        "url": "https://www.radiopolis.gr/feed/",
        "live_url": "http://live24.gr/radio/generic.jsp?sid=169",
        "audience": "low",
        "schedule": "Διάφορες Ώρες"
    },
    {
        "name": "Notos News (Ρόδος)",
        "type": "html",
        "url": "https://www.notosnews.gr/category/diagonismoi/",
        "live_url": "https://www.notosnews.gr/live-radio/",
        "audience": "low",
        "schedule": "Μεσημεριανή Ζώνη"
    },
    {
        "name": "Team FM 102 (Ρέθυμνο)",
        "type": "html",
        "url": "https://goodnet.gr/news-team-fm-102.html",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=1260",
        "audience": "low",
        "schedule": "08:00 - 10:00"
    },
    {
        "name": "Hit Channel (Web)",
        "type": "rss",
        "url": "https://www.hit-channel.com/feed",
        "live_url": "https://www.hit-channel.com/radio",
        "audience": "medium",
        "schedule": "Δείτε το άρθρο"
    },
    {
        "name": "E-Radio (Πανελλαδικό)",
        "type": "html",
        "url": "https://www.e-radio.gr/blog/diagonismoi",
        "live_url": "https://www.e-radio.gr",
        "audience": "high",
        "schedule": "Δείτε το άρθρο"
    }
]

def scrape_contests():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    all_contests = []
    
    # Λέξεις κλειδιά
    positive_keywords = ["κερδίστε", "διαγωνισμός", "πρόσκληση", "δώρο", "μετρητά", "ταξίδι", "συναυλία"]
    negative_keywords = ["νικητές", "έληξε", "αποτελέσματα"]

    print("--- Start Automated Scan ---")

    for station in SOURCES:
        print(f"Scanning: {station['name']} ({station['type']})...")
        
        try:
            items = []
            
            # --- ΣΤΡΑΤΗΓΙΚΗ 1: RSS FEED (Πιο αξιόπιστο) ---
            if station['type'] == 'rss':
                feed = feedparser.parse(station['url'])
                for entry in feed.entries[:10]: # Check last 10 posts
                    items.append({
                        'title': entry.title,
                        'link': entry.link,
                        # Μετατροπή ημερομηνίας σε string
                        'date': datetime.datetime.fromtimestamp(mktime(entry.published_parsed)).strftime("%d/%m/%Y") if hasattr(entry, 'published_parsed') else "Πρόσφατο"
                    })

            # --- ΣΤΡΑΤΗΓΙΚΗ 2: HTML SCRAPING (Fallback) ---
            elif station['type'] == 'html':
                response = requests.get(station['url'], headers=headers, timeout=15)
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                elements = soup.find_all('a', limit=40)
                
                count = 0
                for el in elements:
                    if count >= 5: break
                    text = el.get_text(strip=True)
                    link = el.get('href')
                    
                    if link and text and len(text) > 10:
                        # URL Fix
                        if not link.startswith('http'):
                            from urllib.parse import urljoin
                            link = urljoin(station['url'], link)
                            
                        items.append({'title': text, 'link': link, 'date': datetime.datetime.now().strftime("%d/%m/%Y")})
                        count += 1

            # --- ΦΙΛΤΡΑΡΙΣΜΑ & ΕΠΕΞΕΡΓΑΣΙΑ ---
            for item in items:
                title = item['title']
                link = item['link']

                # 1. Έλεγχος Λέξεων
                if any(bad in title.lower() for bad in negative_keywords): continue
                
                # Πρέπει να περιέχει λέξη κλειδί Ή να προέρχεται από κατηγορία "διαγωνισμοί"
                is_contest = any(good in title.lower() for good in positive_keywords) or "diagonismoi" in station['url']

                if is_contest:
                    # Αποφυγή διπλότυπων
                    if not any(d['link'] == link for d in all_contests):
                        all_contests.append({
                            "title": title,
                            "link": link,
                            "source_name": station['name'],
                            "live_url": station['live_url'],
                            "audience": station['audience'],
                            "schedule": station['schedule'],
                            "found_at": item['date']
                        })

        except Exception as e:
            print(f"Error on {station['name']}: {e}")

    # Ταξινόμηση: Πρώτα οι ευκαιρίες (low), μετά τα άλλα
    priority = {"low": 1, "medium": 2, "high": 3}
    all_contests.sort(key=lambda x: priority.get(x['audience'], 3))

    print(f"Scan complete. Found {len(all_contests)} contests.")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
