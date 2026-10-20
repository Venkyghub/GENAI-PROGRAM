import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable

def get_bbc_headlines():
    url = "https://www.bbc.com/news"
    
    # Header configuration mimicking a typical browser view
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        # Fetch web elements
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        headline_tags = soup.find_all(['h2', 'h3'])
        
        # Initialize the terminal layout table
        table = PrettyTable()
        table.field_names = ["No.", "BBC News Headlines"]
        table.align["BBC News Headlines"] = "l"  # Left-align the headlines column
        
        count = 0
        seen_headlines = set()
        
        # Generic layout labels to discard
        ignored_headers = {
            'most watched', 'also in news', 'most read', 'sport', 
            'features', 'more to explore', 'business', 'technology', 
            'science', 'health', 'entertainment & arts'
        }
        
        for tag in headline_tags:
            headline_text = tag.get_text().strip()
            
            # Filtering rules
            if not headline_text or headline_text in seen_headlines:
                continue
            if headline_text.lower() in ignored_headers:
                continue
            if headline_text.isdigit():
                continue
            
            seen_headlines.add(headline_text)
            count += 1
            
            # Populate the table row instead of standard text print statements
            table.add_row([count, headline_text])
            
            if count == 5:
                break
        
        # Render the final output if elements pass filtering checks
        if count > 0:
            print("\n" + str(table) + "\n")
        else:
            print("\n[Alert] Web page structure changed or headlines failed to load.\n")
                
    except requests.exceptions.RequestException as e:
        print(f"\n[Connection Error] Could not connect to the news site: {e}\n")

if __name__ == "__main__":
    get_bbc_headlines()
