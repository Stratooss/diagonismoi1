import requests
from bs4 import BeautifulSoup
import json
import datetime
import time

# Προσθέσαμε και το e-radio που έχει τεράστια λίστα
TARGET_URLS = [
    "https://www.contest.gr/category/radio-diagonismoi/",
    "https://www.e-radio.gr/blog/diagonismoi", 
]

def scrape_contests():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_contests = []
    
    # Προσθέσαμε περισσότερες λέξεις για να πιάνουμε τα πάντα
    keywords = ["μετρητά", "euro", "ευρώ", "δώρο", "κερδίστε", "διαγωνισμός", "πρόσκληση", "συναυλία", "θεατρ", "τραπέζι", "ταξίδι"]

    print("Ξεκινάει η αναζήτηση...")

    for url in TARGET_URLS:
        print(f"Scanning: {url}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = response.apparent_encoding # Διόρθωση για ελληνικούς χαρακτήρες
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ψάχνουμε γενικά για links που έχουν τίτλο
            elements = soup.find_all('a')
            
            for element in elements:
                text = element.get_text(strip=True)
                link = element.get('href')

                # Αν το link είναι valid και το κείμενο έχει πάνω από 5 γράμματα
                if link and text and len(text) > 5:
                    
                    # Έλεγχος: Περιέχει κάποια λέξη κλειδί;
                    # (Χρησιμοποιούμε lower() για να μην παίζουν ρόλο τα κεφαλαία)
                    if any(word in text.lower() for word in keywords):
                        
                        # Διόρθωση URL αν δεν έχει http
                        full_link = link
                        if not link.startswith('http'):
                            if 'contest.gr' in url:
                                full_link = "https://www.contest.gr" + link
                            elif 'e-radio.gr' in url:
                                full_link = "https://www.e-radio.gr" + link

                        # Αποθήκευση (αν δεν υπάρχει ήδη)
                        if not any(d['link'] == full_link for d in all_contests):
                            all_contests.append({
                                "title": text,
                                "link": full_link,
                                "source": url,
                                "found_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                            })

        except Exception as e:
            print(f"Σφάλμα στο {url}: {e}")
            
    # --- DEBUGGING: Προσθήκη δοκιμαστικού αν δεν βρεθεί τίποτα ---
    if len(all_contests) == 0:
        print("Δεν βρέθηκαν διαγωνισμοί, προσθήκη δοκιμαστικού.")
        all_contests.append({
            "title": "ΔΟΚΙΜΑΣΤΙΚΗ ΕΓΓΡΑΦΗ: Ο μηχανισμός λειτουργεί!",
            "link": "https://google.com",
            "source": "System Check",
            "found_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        })

    print(f"Βρέθηκαν {len(all_contests)} εγγραφές.")
    
    with open('contests.json', 'w', encoding='utf-8') as f:
        json.dump(all_contests, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    scrape_contests()
