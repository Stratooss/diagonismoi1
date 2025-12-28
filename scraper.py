import requests
from bs4 import BeautifulSoup
import feedparser
import json
import datetime
from time import mktime
import re

# --- ΡΥΘΜΙΣΕΙΣ ---
MAX_DAYS_OLD = 7  # Πόσες μέρες θεωρείται "ενεργός" ένας διαγωνισμός;
# (Στα ραδιόφωνα συνήθως κρατάνε 3-5 μέρες, οπότε το 7 είναι ασφαλές όριο)

SOURCES = [
    {
        "name": "Radio Polis 99.4 (Λάρισα)",
        "type": "rss",
        "url": "https://www.radiopolis.gr/category/diagonismoi/feed/",
        "live_url": "http://live24.gr/radio/generic.jsp?sid=169",
        "audience": "low",
        "schedule": "Δείτε το άρθρο"
    },
    {
        "name": "Fly FM 89.7 (Σπάρτη)",
        "type": "html",
        "url": "https://flynews.gr/category/fly-fm-897/",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=792",
        "audience": "low",
        "schedule": "Πρωινή Ζώνη"
    },
    {
        "name": "Anemos 95.6 (Σάμος)",
        "type": "html",
        "url": "https://anemos956.gr/category/news/", 
        "live_url": "https://live24.gr/radio/generic.jsp?sid=498",
        "audience": "low", 
        "schedule": "09:00 - 12:00"
    },
    {
        "name": "Notos News (Ρόδος)",
        "type": "rss",
        "url": "https://www.notosnews.gr/category/diagonismoi/feed/",
        "live_url": "https://www.notosnews.gr/live-radio/",
        "audience": "low",
        "schedule": "Μεσημεριανή Ζώνη"
    },
    {
        "name": "Hit Channel",
        "type": "rss",
        "url": "https://www.hit-channel.com/category/diagonismoi/feed",
        "live_url": "https://www.hit-channel.com/radio",
        "audience": "medium",
        "schedule": "Δείτε το άρθρο"
    },
    {
        "name": "E-Radio (Blog)",
        "type": "html",
        "url": "https://www.e-radio.gr/blog/diagonismoi",
        "live_url": "https://www.e-radio.gr",
        "audience": "high",
        "schedule": "Check Link"
    }
]

def parse_date(entry):
    """Βοηθητική συνάρτηση για να βρίσκουμε πότε ανέβηκε το άρθρο"""
    try:
        if hasattr(entry, 'published_parsed'):
            return datetime.datetime.fromtimestamp(mktime(entry.published_parsed))
        elif hasattr(entry, 'updated_parsed'):
            return datetime.datetime.fromtimestamp(mktime(entry.updated_parsed))
        else:
            return datetime.datetime.now() # Αν δεν βρούμε ημερομηνία, υποθέτουμε τώρα
    except:
        return datetime.datetime.now()

def scrape_contests():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    all_contests = []
    
    # Λέξεις που δείχνουν ότι ο διαγωνισμός είναι ενεργός
    required_keywords = ["κερδίστε", "διαγωνισμός", "κληρωση", "δωροεπιταγ", "προσκλησεις", "διημερο", "ταξιδι"]
    
    # Λέξεις που δείχνουν λήξη ή άσχετο περιεχόμενο
    negative_keywords = [
        "νικητές", "έληξε", "αποτελέσματα", "κληρώθηκαν", "ολοκληρώθηκε", # Λήξη
        "συνέντευξη", "παρουσίαση", "κυκλοφορεί", "νέο τραγούδι", "live", "πρόγραμμα" # Άσχετα
    ]

    now = datetime.datetime.now()
    print(f"--- Start Scan: {now.strftime('%d/%m/%Y %H:%M')} ---")

    for station in SOURCES:
        try:
            items = []
            
            # === RSS Logic (Με ακριβή ημερομηνία) ===
            if station['type'] == 'rss':
                feed = feedparser.parse(station['url'])
                for entry in feed.entries[:10]:
                    
                    # 1. Έλεγχος Ημερομηνίας (Freshness Check)
                    pub_date = parse_date(entry)
                    days_diff = (now - pub_date).days
                    
                    # Αν είναι παλιότερο από το όριο, το προσπερνάμε (ΕΚΤΟΣ αν είναι pinned)
                    if days_diff > MAX_DAYS_OLD:
                        continue 

                    items.append({
                        'title': entry.title,
                        'link': entry.link,
                        'date_obj': pub_date,
                        'date_str': pub_date.strftime("%d/%m/%Y")
                    })

            # === HTML Logic (Υποθέτουμε ότι τα πάνω-πάνω είναι φρέσκα) ===
            elif station['type'] == 'html':
                response = requests.get(station['url'], headers=headers, timeout=15)
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                
                elements = soup.find_all(['h2', 'h3', 'h4', 'a'], limit=40)
                count = 0
                
                for el in elements:
                    if count >= 4: break # Παίρνουμε μόνο τα 4 πρώτα (τα πιο πρόσφατα)
                    
                    if el.name == 'a': link_tag = el
                    else: link_tag = el.find('a')
                    
                    if not link_tag: continue

                    text = link_tag.get_text(strip=True)
                    link = link_tag.get('href')
                    
                    if link and text and len(text) > 10:
                        if not link.startswith('http'):
                            from urllib.parse import urljoin
                            link = urljoin(station['url'], link)
                        
                        # Στο HTML δεν ξέρουμε ακριβή ημερομηνία, βάζουμε τη σημερινή
                        items.append({
                            'title': text, 
                            'link': link, 
                            'date_obj': now,
                            'date_str': now.strftime("%d/%m/%Y")
                        })
                        count += 1

            # === ΚΕΝΤΡΙΚΟ ΦΙΛΤΡΑΡΙΣΜΑ ===
            for item in items:
                title_lower = item['title'].lower()
                link = item['link']

                # Φίλτρο 1: Αρνητικές Λέξεις
                if any(bad in title_lower for bad in negative_keywords): continue

                # Φίλτρο 2: Λέξεις κλειδιά (ή αν προέρχεται από feed διαγωνισμών)
                is_contest_feed = "diagonismoi" in station['url'] or "blog/diagonismoi" in station['url']
                has_keyword = any(good in title_lower for good in required_keywords)

                if has_keyword or (is_contest_feed and "νέα" not in title_lower):
                    
                    # Φίλτρο 3: Έλεγχος αν ο τίτλος έχει παλιά ημερομηνία (Regex)
                    # Π.χ. Αν λέει "έως 20/12" και έχουμε 28/12, το πετάμε
                    # (Αυτό είναι πολύπλοκο, οπότε βασιζόμαστε κυρίως στην ημερομηνία δημοσίευσης προς το παρόν)
                    
                    if not any(d['link'] == link for d in all_contests):
                        all_contests.append({
                            "title": item['title'],
                            "link": link,
                            "source_name": station['name'],
                            "live_url": station['live_url'],
                            "audience": station['audience'],
                            "schedule": station['schedule'],
                            "found_at": item['date_str']
                        })

        except Exception as e:
            print(f"Error on {station['name']}: {e}")

    # Ταξινόμηση
    priority = {"low": 1, "medium": 2, "high": 3}
    all_contests.sort(key=lambda x: priority.get(x['audience'], 3))

    print(f"Scan complete. Kept {len(all_contests)} fresh contests.")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
