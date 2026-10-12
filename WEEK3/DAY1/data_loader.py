
import json
import time
import requests

from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.tn.gov.in/"
LIST_URL = urljoin(
    BASE_URL,
    "scheme_list.php?dep_id=Mg=="
)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def extract_text(soup):
    # Remove elements that usually contain navigation
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    # Prefer the main content area when available
    main = (
        soup.find("main")
        or soup.find(id="main")
        or soup.find(id="content")
        or soup.find("body")
        or soup
    )

    return main.get_text(separator="\n", strip=True)


def main():
    print("Downloading scheme listing page...")

    response = session.get(LIST_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    schemes = []
    seen_urls = set()

    # Find individual scheme detail pages
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()

        if "scheme_details.php" not in href:
            continue

        scheme_url = urljoin(LIST_URL, href)

        if scheme_url in seen_urls:
            continue

        seen_urls.add(scheme_url)

        scheme_name = link.get_text(" ", strip=True)

        if not scheme_name:
            continue

        print(f"Downloading: {scheme_name}")

        try:
            detail_response = session.get(
                scheme_url,
                timeout=30
            )
            detail_response.raise_for_status()

            detail_soup = BeautifulSoup(
                detail_response.text,
                "html.parser"
            )

            details = extract_text(detail_soup)

            schemes.append({
                "scheme_name": scheme_name,
                "url": scheme_url,
                "details": details
            })

        except requests.RequestException as error:
            print(f"Failed: {scheme_name} - {error}")

        # Avoid sending requests too quickly
        time.sleep(0.5)

    # Save structured data
    json_file = OUTPUT_DIR / "schemes.json"
    json_file.write_text(
        json.dumps(
            schemes,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # Save readable text
    text_file = OUTPUT_DIR / "government_schemes.txt"

    with text_file.open("w", encoding="utf-8") as file:
        for scheme in schemes:
            file.write(f"SCHEME: {scheme['scheme_name']}\n")
            file.write(f"URL: {scheme['url']}\n")
            file.write(scheme["details"])
            file.write("\n\n" + "=" * 70 + "\n\n")

    print("\nDataLoader completed!")
    print(f"Scheme pages collected: {len(schemes)}")
    print(f"JSON file: {json_file.resolve()}")
    print(f"Text file: {text_file.resolve()}")


if __name__ == "__main__":
    main()
