
import requests
from bs4 import BeautifulSoup

url = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

for link in soup.find_all("a", href=True):
    name = link.get_text(" ", strip=True)
    href = link["href"]

    if name:
        print(f"Scheme/link: {name}")
        print(f"URL: {href}")
        print("-" * 50)
