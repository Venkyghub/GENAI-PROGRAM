
import json
from pathlib import Path

INPUT_FILE = Path("data/extracted_entities.json")
OUTPUT_FILE = Path("data/graph_data.json")


def clean(value):
    if not value:
        return None

    value = str(value).strip()
    return value if value else None


def main():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        schemes = json.load(file)

    nodes = {}
    relationships = []

    def add_node(label, name, **properties):
        if not name:
            return None

        # Reuse nodes with the same label and name
        key = (label, name.strip())

        if key not in nodes:
            nodes[key] = {
                "id": f"{label}:{name.strip()}",
                "label": label,
                "name": name.strip(),
                "properties": {}
            }

        for prop, value in properties.items():
            if value is not None:
                nodes[key]["properties"][prop] = value

        return nodes[key]["id"]

    def add_relationship(source, relation, target):
        if source and target:
            relationships.append({
                "source": source,
                "type": relation,
                "target": target
            })

    for scheme in schemes:
        scheme_name = clean(scheme.get("scheme_name"))

        if not scheme_name:
            continue

        scheme_id = add_node(
            "Scheme",
            scheme_name,
            sponsored_by=clean(scheme.get("sponsored_by")),
            funding_pattern=clean(scheme.get("funding_pattern")),
            benefit_type=clean(scheme.get("benefit_type")),
            description=clean(scheme.get("description")),
            how_to_avail=clean(scheme.get("how_to_avail")),
            source_url=clean(scheme.get("source_url"))
        )

        # Scheme -> Department
        department = clean(scheme.get("department"))

        if department:
            department_id = add_node("Department", department)
            add_relationship(
                scheme_id, "BELONGS_TO", department_id
            )

        # Scheme -> Beneficiary
        beneficiary = clean(scheme.get("beneficiaries"))

        if beneficiary:
            beneficiary_id = add_node(
                "Beneficiary", beneficiary
            )
            add_relationship(
                scheme_id, "HAS_BENEFICIARY", beneficiary_id
            )

        # Scheme -> Benefit type
        benefit = clean(scheme.get("benefit_type"))

        if benefit:
            benefit_id = add_node("BenefitType", benefit)
            add_relationship(
                scheme_id, "PROVIDES_BENEFIT_TYPE", benefit_id
            )

        # Scheme -> District, only when specified
        district = clean(scheme.get("district"))

        if district:
            district_id = add_node("District", district)
            add_relationship(
                scheme_id, "AVAILABLE_IN", district_id
            )

    graph_data = {
        "nodes": list(nodes.values()),
        "relationships": relationships
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            graph_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("Relationship Mapping completed!")
    print("Input schemes:", len(schemes))
    print("Unique nodes:", len(nodes))
    print("Relationships:", len(relationships))
    print("Saved to:", OUTPUT_FILE.resolve())

    print("\nSample relationships:")
    for relationship in relationships[:10]:
        print(relationship)


if __name__ == "__main__":
    main()
