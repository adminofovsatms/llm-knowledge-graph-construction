from agentic_pipeline.config import graph, PERSON_NAME
from datetime import datetime

# Helper function to convert injury_date string to Neo4j-compatible format
def parse_neo4j_date(raw_date: str) -> str:
    try:
        # Case: "2013-11-21 08:30PM"
        dt = datetime.strptime(raw_date, "%Y-%m-%d %I:%M%p")
        return dt.date().isoformat()
    except:
        try:
            # Case: "2013-11-21"
            dt = datetime.strptime(raw_date, "%Y-%m-%d")
            return dt.date().isoformat()
        except:
            # Fallback if date is missing or malformatted
            return "1900-01-01"

class InjuryAgent:
    def __init__(self):
        self.graph = graph

    def upsert(self, injury_data):
        query = """
        MERGE (i:Injury {injury_id: $injury_id})
        SET i.injury_date = date($injury_date),
            i.pain_level = $pain_level,
            i.pain_description = $pain_description
        WITH i
        MATCH (p:Person {name: $person})
        MERGE (p)-[:HAD_INJURY]->(i)
        RETURN i
        """

        return self.graph.query(query, {
            "injury_id": injury_data["injury_id"],
            "injury_date": parse_neo4j_date(injury_data["injury_date"]),
            "pain_level": injury_data.get("pain_level", "Moderate"),
            "pain_description": injury_data.get("pain_description", ""),
            "person": PERSON_NAME
        })