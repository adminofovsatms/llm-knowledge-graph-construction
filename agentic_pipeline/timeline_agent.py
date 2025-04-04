from agentic_pipeline.config import graph, PERSON_NAME

class TimelineAgent:
    def __init__(self):
        self.graph = graph

    def filter_by_month(self, year, month):
        cypher = """
        MATCH (p:Person {name: $name})-[:HAD_INJURY]->(i:Injury)
        WHERE date(i.injury_date).year = $year AND date(i.injury_date).month = $month
        OPTIONAL MATCH (i)-[:LOCATED_IN]->(b:BodyPart)
        OPTIONAL MATCH (i)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
        RETURN i, b, d
        """
        return self.graph.query(cypher, {"name": PERSON_NAME, "year": year, "month": month})