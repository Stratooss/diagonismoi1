import requests
from bs4 import BeautifulSoup
import feedparser
import json
import datetime
from time import mktime

# --- ΛΙΣΤΑ ΣΤΟΧΩΝ (STRICT CATEGORY FEEDS) ---
# Αλλάξαμε τα URLS για να δείχνουν ΜΟΝΟ την κατηγορία διαγωνισμών
SOURCES = [
    {
        "name": "Radio Polis 99.4 (Λάρισα)",
        "type": "rss",
        # URL που δίνει ΜΟΝΟ διαγωνισμούς, όχι ειδήσεις
        "url": "https://www.radiopolis.gr/category/diagonismoi/feed/",
        "live_url": "http://live24.gr/radio/generic.jsp?sid=169",
        "audience": "low",
        "schedule": "Δείτε το άρθρο"
    },
    {
        "name": "Fly FM 89.7 (Σπάρτη)",
        "type": "html", # Γυρίσαμε σε HTML για καλύτερο φιλτράρισμα εδώ
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

def scrape_contests():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    all_contests = []
    
    # --- ΦΙΛΤΡΑ (STRICT) ---
    # Πρέπει ΟΠΩΣΔΗΠΟΤΕ να υπάρχει μια από αυτές τις λέξεις στον τίτλο
    required_keywords = ["κερδίστε", "διαγωνισμός", "κληρωση", "δωροεπιταγ", "προσκλησεις", "διημερο", "ταξιδι"]
    
    # Λέξεις που πετάμε αμέσως (Ειδήσεις, Αποτελέσματα)
    negative_keywords = ["νικητές", "έληξε", "αποτελέσματα", "συνέντευξη", "παρουσίαση", "κυκλοφορεί", "νέο τραγούδι", "είδηση", "καιρός", "πρόγραμμα", "live"]

    print("--- Start Strict Scan ---")

    for station in SOURCES:
        print(f"Scanning: {station['name']} ({station['type']})...")
        
        try:
            items = []
            
            # --- RSS LOGIC ---
            if station['type'] == 'rss':
                feed = feedparser.parse(station['url'])
                for entry in feed.entries[:8]:
                    items.append({
                        'title': entry.title,
                        'link': entry.link,
                        'date': datetime.datetime.fromtimestamp(mktime(entry.published_parsed)).strftime("%d/%m/%Y") if hasattr(entry, 'published_parsed') else "Πρόσφατο"
                    })

            # --- HTML SCRAPING LOGIC ---
            elif station['type'] == 'html':
                response = requests.get(station['url'], headers=headers, timeout=15)
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Ψάχνουμε συνδέσμους μέσα σε τίτλους (h2, h3) ή άρθρα
                elements = soup.find_all(['h2', 'h3', 'h4', 'a'], limit=50)
                
                count = 0
                for el in elements:
                    if count >= 5: break
                    
                    # Αν είναι Tag 'a', πάρε το κείμενο, αλλιώς ψάξε το 'a' μέσα του
                    if el.name == 'a':
                        link_tag = el
                    else:
                        link_tag = el.find('a')
                    
                    if not link_tag: continue

                    text = link_tag.get_text(strip=True)
                    link = link_tag.get('href')
                    
                    if link and text and len(text) > 10:
                        # URL Fix
                        if not link.startswith('http'):
                            from urllib.parse import urljoin
                            link = urljoin(station['url'], link)
                            
                        items.append({'title': text, 'link': link, 'date': datetime.datetime.now().strftime("%d/%m/%Y")})
                        count += 1

            # --- ΕΠΕΞΕΡΓΑΣΙΑ & ΦΙΛΤΡΑΡΙΣΜΑ ---
            for item in items:
                title = item['title'].lower() # Μετατροπή σε μικρά για έλεγχο
                link = item['link']

                # 1. Βήμα: Έλεγχος Αρνητικών (Stop Words)
                if any(bad in title for bad in negative_keywords): 
                    continue # Είναι είδηση ή αποτελέσματα, πέτα το.

                # 2. Βήμα: Έλεγχος Θετικών (Must Have)
                # Ειδική εξαίρεση: Αν το URL της πηγής έχει τη λέξη "diagonismoi", είμαστε πιο ελαστικοί
                is_explicit_contest = any(good in title for good in required_keywords)
                is_from_contest_feed = "diagonismoi" in station['url'] or "blog/diagonismoi" in station['url']

                if is_explicit_contest or (is_from_contest_feed and "νέα" not in title):
                    
                    # Αποφυγή διπλότυπων
                    if not any(d['link'] == link for d in all_contests):
                        all_contests.append({
                            "title": item['title'], # Κρατάμε τον αρχικό τίτλο (με κεφαλαία)
                            "link": link,
                            "source_name": station['name'],
                            "live_url": station['live_url'],
                            "audience": station['audience'],
                            "schedule": station['schedule'],
                            "found_at": item['date']
                        })

        except Exception as e:
            print(f"Error on {station['name']}: {e}")

    # Ταξινόμηση
    priority = {"low": 1, "medium": 2, "high": 3}
    all_contests.sort(key=lambda x: priority.get(x['audience'], 3))

    print(f"Scan complete. Found {len(all_contests)} valid contests.")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
