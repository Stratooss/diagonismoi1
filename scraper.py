import requests
from bs4 import BeautifulSoup
import json
import datetime
import os

# Λίστα με URL για σκανάρισμα
# Μπορείς να προσθέσεις όσα θέλεις εδώ
TARGET_URLS = [
    "https://www.contest.gr/category/radio-diagonismoi/",
    # Παράδειγμα: Προσθέτεις εδώ κατηγορίες "Νέα" από τοπικούς σταθμούς
    # "https://www.radiopolis.gr/category/diagonismoi/",
]

def scrape_contests():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_contests = []
    
    # Λέξεις που ψάχνουμε
    keywords = ["μετρητά", "euro", "ευρώ", "δώρο", "κερδίστε", "διαγωνισμός", "ταξίδι", "πρόσκληση"]

    print("Ξεκινάει η αναζήτηση...")

    for url in TARGET_URLS:
        print(f"Scanning: {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ψάχνουμε για τίτλους άρθρων και links
            # Προσαρμόζεται για να πιάνει τα περισσότερα Wordpress/News sites
            elements = soup.find_all(['h2', 'h3', 'h4', 'a'])
            
            for element in elements:
                text = element.get_text(strip=True)
                
                # Έλεγχος αν είναι link (είτε το ίδιο το tag, είτε ο γονέας του)
                link = element.get('href')
                if not link and element.parent.name == 'a':
                    link = element.parent.get('href')

                # Αν βρέθηκε κείμενο, link και περιέχει λέξη-κλειδί
                if link and text and len(text) > 10 and any(word in text.lower() for word in keywords):
                    
                    # Διόρθωση relative URLs
                    if not link.startswith('http'):
                        if url.endswith('/'):
                            link = url + link
                        else: # Απλή προσπάθεια διόρθωσης
                            from urllib.parse import urljoin
                            link = urljoin(url, link)

                    # Αποφυγή διπλότυπων στη λίστα
                    if not any(d['link'] == link for d in all_contests):
                        all_contests.append({
                            "title": text[:120] + "..." if len(text) > 120 else text,
                            "link": link,
                            "source": url,
                            "found_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        })

        except Exception as e:
            print(f"Σφάλμα στο {url}: {e}")
            
    # Αποθήκευση αποτελεσμάτων
    print(f"Βρέθηκαν {len(all_contests)} διαγωνισμοί.")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
