import requests
from bs4 import BeautifulSoup
import json
import datetime

# --- ΡΥΘΜΙΣΕΙΣ ΣΤΑΘΜΩΝ ---
# Εδώ ορίζουμε τα sites που παρακολουθούμε και τα χαρακτηριστικά τους
SOURCES = [
    {
        "name": "Anemos 95.6 (Σάμος)",
        "scrape_url": "https://anemos956.gr/category/news/",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=498",
        "audience": "low", # low = Μεγάλη ευκαιρία
        "schedule": "Πρωινή Ζώνη (09:00 - 12:00)"
    },
    {
        "name": "Radio Polis 99.4 (Λάρισα)",
        "scrape_url": "https://www.radiopolis.gr/category/diagonismoi/",
        "live_url": "http://live24.gr/radio/generic.jsp?sid=169",
        "audience": "low",
        "schedule": "09:00 - 11:00 & 18:00 - 20:00"
    },
    {
        "name": "Fly FM 89.7 (Σπάρτη)",
        "scrape_url": "https://flynews.gr/category/fly-fm-897/",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=792",
        "audience": "low",
        "schedule": "Πρωινό Magazino (08:00 - 11:00)"
    },
    {
        "name": "Team FM 102 (Ρέθυμνο)",
        "scrape_url": "https://goodnet.gr/news-team-fm-102.html",
        "live_url": "https://live24.gr/radio/generic.jsp?sid=1260",
        "audience": "low",
        "schedule": "Πρώτη Γραμμή (08:00 - 10:00)"
    },
    {
        "name": "Hit Channel (Αθήνα/Web)",
        "scrape_url": "https://www.hit-channel.com/diagonismoi",
        "live_url": "https://www.hit-channel.com/radio",
        "audience": "medium",
        "schedule": "Δείτε το άρθρο"
    },
    {
        "name": "Notos News (Ρόδος)",
        "scrape_url": "https://www.notosnews.gr/category/diagonismoi/",
        "live_url": "https://www.notosnews.gr/live-radio/",
        "audience": "low",
        "schedule": "Μεσημεριανή Ζώνη"
    },
     {
        "name": "City Portal (Θεσσαλονίκη)",
        "scrape_url": "https://cityportal.gr/category/diagonismoi/",
        "live_url": "https://cityportal.gr/", # Δεν είναι σταθμός, είναι portal
        "audience": "high",
        "schedule": "Διάφορες Ώρες"
    },
    # Το E-radio για να πιάνουμε τα πάντα (Υψηλός ανταγωνισμός)
    {
        "name": "E-Radio (Πανελλαδικό)",
        "scrape_url": "https://www.e-radio.gr/blog/diagonismoi",
        "live_url": "https://www.e-radio.gr",
        "audience": "high",
        "schedule": "Δείτε το άρθρο"
    }
]

def scrape_contests():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_contests = []
    
    # Λέξεις κλειδιά
    positive_keywords = ["κερδίστε", "διαγωνισμός", "πρόσκληση", "δώρο", "μετρητά", "ταξίδι", "τραπέζι", "συναυλία"]
    negative_keywords = ["νικητές", "έληξε", "αποτελέσματα", "κληρώθηκαν", "παλαιότεροι"]

    print("--- Start Scraping ---")

    for station in SOURCES:
        url = station['scrape_url']
        print(f"Checking: {station['name']}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Παίρνουμε τα πρώτα 20 links
            elements = soup.find_all('a', limit=60)
            
            count_added = 0
            
            for element in elements:
                if count_added >= 4: break # Max 4 διαγωνισμοί ανά σταθμό

                text = element.get_text(strip=True)
                link = element.get('href')

                if not link or not text or len(text) < 10: continue

                # Φίλτρα
                if any(bad in text.lower() for bad in negative_keywords): continue
                if any(good in text.lower() for good in positive_keywords):
                    
                    # URL Cleanup
                    full_link = link
                    if not link.startswith('http'):
                        if url.endswith('/'): full_link = url + link
                        else:
                             from urllib.parse import urlparse
                             parsed_uri = urlparse(url)
                             base = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
                             full_link = base + link

                    # Αποφυγή Διπλότυπων
                    if not any(d['link'] == full_link for d in all_contests):
                        all_contests.append({
                            "title": text,
                            "link": full_link,           # Link διαγωνισμού
                            "source_name": station['name'],
                            "live_url": station['live_url'], # Link για να ακούσεις
                            "audience": station['audience'], # low/medium/high
                            "schedule": station['schedule'], # Ώρα
                            "found_at": datetime.datetime.now().strftime("%d/%m/%Y")
                        })
                        count_added += 1

        except Exception as e:
            print(f"Error on {station['name']}: {e}")

    # Ταξινόμηση: Πρώτα τα LOW audience (Ευκαιρίες), μετά τα άλλα
    priority_order = {"low": 1, "medium": 2, "high": 3}
    all_contests.sort(key=lambda x: priority_order.get(x['audience'], 3))

    print(f"Total contests: {len(all_contests)}")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
