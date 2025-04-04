from agentic_pipeline.config import graph, BODY_PART_POSITIONS, PERSON_NAME

class BodyPartAgent:
    def __init__(self):
        self.graph = graph

    def upsert(self, name, side="Center"):
        key = f"{side}-{name}"
        x, y = BODY_PART_POSITIONS.get(name, (0, 0))

        cypher = """
        MERGE (b:BodyPart {body_part_id: $id})
        SET b.name = $name, b.side = $side, b.x = $x, b.y = $y
        WITH b
        MATCH (p:Person {name: $person})
        MERGE (p)-[:HAS_BODY_PART]->(b)
        RETURN b
        """
        return self.graph.query(cypher, {
            "id": f"BODYPART-{key}",
            "name": name,
            "side": side,
            "x": x,
            "y": y,
            "person": PERSON_NAME
        })