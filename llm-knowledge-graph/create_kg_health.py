import os
import pandas as pd
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# File path
CSV_PATH =  "llm-knowledge-graph/data/course/health-csv/sleep_cycle_productivity.csv"

llm = ChatOpenAI(   
    openai_api_key=os.getenv('OPENAI_API_KEY'), 
    model_name="gpt-3.5-turbo"
)

graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# Load CSV data
df = pd.read_csv(CSV_PATH)

# Process each row in the CSV
for index, row in df.iterrows():
    print(f"Processing row {index+1}/{len(df)}")
    
    # Create Person node (if not exists)
    person_properties = {
        "person_id": row["Person_ID"],
        "age": row["Age"],
        "gender": row["Gender"]
    }
    
    graph.query("""
        MERGE (p:Person {id: $person_id})
        SET p.age = $age,
            p.gender = $gender
        RETURN p
    """, person_properties)
    
    # Create DailyRecord node
    daily_record_properties = {
        "person_id": row["Person_ID"],
        "date": row["Date"],
        "work_hours": row["Work Hours (hrs/day)"],
        "productivity_score": row["Productivity Score"],
        "mood_score": row["Mood Score"],
        "record_id": f"{row['Person_ID']}_{row['Date']}"  # Unique ID for the record
    }
    
    graph.query("""
        MATCH (p:Person {id: $person_id})
        MERGE (d:DailyRecord {id: $record_id})
        SET d.date = $date,
            d.work_hours = $work_hours,
            d.productivity_score = $productivity_score,
            d.mood_score = $mood_score
        MERGE (p)-[:RECORDED]->(d)
        RETURN d
    """, daily_record_properties)
    
    # Create SleepData node
    sleep_properties = {
        "record_id": f"{row['Person_ID']}_{row['Date']}",
        "start_time": row["Sleep Start Time"],
        "end_time": row["Sleep End Time"],
        "duration": row["Total Sleep Hours"],
        "quality": row["Sleep Quality"],
        "sleep_id": f"{row['Person_ID']}_{row['Date']}_sleep"
    }
    
    graph.query("""
        MATCH (d:DailyRecord {id: $record_id})
        MERGE (s:SleepData {id: $sleep_id})
        SET s.start_time = $start_time,
            s.end_time = $end_time,
            s.duration = $duration,
            s.quality = $quality
        MERGE (d)-[:HAS_SLEEP_DATA]->(s)
        RETURN s
    """, sleep_properties)
    
    # Create CaffeineIntake node
    caffeine_properties = {
        "record_id": f"{row['Person_ID']}_{row['Date']}",
        "amount": row["Caffeine Intake (mg)"],
        "caffeine_id": f"{row['Person_ID']}_{row['Date']}_caffeine"
    }
    
    graph.query("""
        MATCH (d:DailyRecord {id: $record_id})
        MERGE (c:CaffeineIntake {id: $caffeine_id})
        SET c.amount = $amount
        MERGE (d)-[:HAS_CAFFEINE_INTAKE]->(c)
        RETURN c
    """, caffeine_properties)
    
    # Create StressLevel node
    stress_properties = {
        "record_id": f"{row['Person_ID']}_{row['Date']}",
        "level": row["Stress Level"],
        "stress_id": f"{row['Person_ID']}_{row['Date']}_stress"
    }
    
    graph.query("""
        MATCH (d:DailyRecord {id: $record_id})
        MERGE (s:StressLevel {id: $stress_id})
        SET s.level = $level
        MERGE (d)-[:HAS_STRESS_LEVEL]->(s)
        RETURN s
    """, stress_properties)
    
    # Create Exercise node
    exercise_properties = {
        "record_id": f"{row['Person_ID']}_{row['Date']}",
        "duration": row["Exercise (mins/day)"],
        "exercise_id": f"{row['Person_ID']}_{row['Date']}_exercise"
    }
    
    graph.query("""
        MATCH (d:DailyRecord {id: $record_id})
        MERGE (e:Exercise {id: $exercise_id})
        SET e.duration = $duration
        MERGE (d)-[:INCLUDED_EXERCISE]->(e)
        RETURN e
    """, exercise_properties)
    
    # Create ScreenTime node
    screen_properties = {
        "record_id": f"{row['Person_ID']}_{row['Date']}",
        "duration": row["Screen Time Before Bed (mins)"],
        "screen_id": f"{row['Person_ID']}_{row['Date']}_screen"
    }
    
    graph.query("""
        MATCH (d:DailyRecord {id: $record_id})
        MERGE (s:ScreenTime {id: $screen_id})
        SET s.duration = $duration
        MERGE (d)-[:HAD_SCREEN_TIME]->(s)
        RETURN s
    """, screen_properties)

print("Data import complete!")