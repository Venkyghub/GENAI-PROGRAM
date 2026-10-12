
import json
from pathlib import Path

file_path = Path("data/schemes.json")

with file_path.open("r", encoding="utf-8") as file:
    schemes = json.load(file)

print("Total scheme records:", len(schemes))

for index, scheme in enumerate(schemes[:3], start=1):
    details = scheme.get("details", "")

    print("\n" + "=" * 60)
    print(f"SCHEME {index}: {scheme.get('scheme_name')}")
    print("URL:", scheme.get("url"))
    print("Details characters:", len(details))
    print("\nExtracted content:")
    print(details[:1500])
