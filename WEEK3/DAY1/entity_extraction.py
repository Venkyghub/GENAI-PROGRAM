
import json
from pathlib import Path

INPUT_FILE = Path("data/schemes.json")
OUTPUT_FILE = Path("data/extracted_entities.json")

# Website field labels mapped to Python field names
FIELD_MAP = {
    "Concerned Department:": "department",
    "Concerned District:": "district",
    "Organisation Name:": "organisation",
    "Scheme Title/Name:": "scheme_name",
    "Associated Scheme:": "associated_scheme",
    "Sponsered By:": "sponsored_by",
    "Funding Pattern:": "funding_pattern",
    "Beneficiaries:": "beneficiaries",
    "Types of Benefits:": "benefit_type",
    "Income:": "income",
    "Age From:": "age_from",
    "Age To:": "age_to",
    "Community:": "community",
    "How To avail:": "how_to_avail",
    "Validity of the Scheme:": "validity",
    "Introduced On:": "introduced_on",
    "Description:": "description",
    "Scheme Type:": "scheme_type",
    "Uploaded File:": "uploaded_file"
}

# Sort labels by length to avoid partial matching
LABELS = sorted(FIELD_MAP, key=len, reverse=True)


# Headings that mark a new section but are not entity fields
BOUNDARY_LABELS = [
    "Scheme Details:",
    "Eligibility criteria:"
]


def extract_fields(details):
    lines = [
        line.strip()
        for line in details.splitlines()
        if line.strip()
    ]

    result = {field: None for field in FIELD_MAP.values()}
    current_field = None

    
    for line in lines:
        # Stop appending text when a section heading is encountered
        if any(line.startswith(label) for label in BOUNDARY_LABELS):
            current_field = None
            continue

        matched_label = None
 

        for label in LABELS:
            if line.startswith(label):
                matched_label = label
                break

        if matched_label:
            current_field = FIELD_MAP[matched_label]
            remaining = line[len(matched_label):].strip()

            if remaining:
                result[current_field] = remaining

        elif current_field:
            # Append multiline field values
            if result[current_field]:
                result[current_field] += " " + line
            else:
                result[current_field] = line

    # Remove placeholder values
    for key, value in result.items():
        if value and value.lower() in ("na", "n/a", "-"):
            result[key] = None

    return result


def main():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        schemes = json.load(file)

    extracted_entities = []

    for scheme in schemes:
        fields = extract_fields(scheme["details"])

        # Use listing name as the canonical scheme name
        fields["scheme_name"] = scheme["scheme_name"]
        fields["source_url"] = scheme["url"]

        extracted_entities.append(fields)

    OUTPUT_FILE.write_text(
        json.dumps(
            extracted_entities,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("Entity Extraction completed!")
    print("Total schemes processed:", len(extracted_entities))
    print("Output:", OUTPUT_FILE)

    print("\nFirst extracted record:")
    print(json.dumps(
        extracted_entities[0],
        ensure_ascii=False,
        indent=2
    ))


if __name__ == "__main__":
    main()
