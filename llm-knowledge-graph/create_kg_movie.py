import os
import pandas as pd
import re
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# File path - update this with your CSV path
CSV_PATH = "llm-knowledge-graph/data/course/health-csv/imdb_movies.csv"

llm = ChatOpenAI(   
    openai_api_key=os.getenv('OPENAI_API_KEY'), 
    model_name="gpt-3.5-turbo"
)

graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# Function to clean text and handle special characters
def clean_text(text):
    if pd.isna(text) or text is None:
        return ""
    # Remove special characters but keep spaces
    return re.sub(r'[^\w\s]', '', str(text)).strip()

# Load CSV data
df = pd.read_csv(CSV_PATH)

# Process each row in the CSV
for index, row in df.iterrows():
    print(f"Processing row {index+1}/{len(df)}")
    
    # Create Movie node
    movie_properties = {
        "name": row["names"],
        "release_date": row["date_x"],
        "score": row["score"],
        "overview": row["overview"],
        "budget": row["budget_x"],
        "revenue": row["revenue"],
        "movie_id": clean_text(row["names"]) + "_" + str(row["date_x"])  # Creating a unique ID
    }
    
    # Handle null values
    for key, value in movie_properties.items():
        if pd.isna(value):
            movie_properties[key] = None
    
    # Create Movie node
    graph.query("""
        MERGE (m:Movie {id: $movie_id})
        SET m.name = $name,
            m.release_date = $release_date,
            m.score = $score,
            m.overview = $overview,
            m.budget = $budget,
            m.revenue = $revenue
        RETURN m
    """, movie_properties)
    
    # Process Country
    if not pd.isna(row["country"]):
        countries = str(row["country"]).split(",")
        for country in countries:
            country = country.strip()
            if country:
                country_properties = {
                    "movie_id": movie_properties["movie_id"],
                    "country_name": country
                }
                
                graph.query("""
                    MATCH (m:Movie {id: $movie_id})
                    MERGE (c:Country {name: $country_name})
                    MERGE (m)-[:PRODUCED_IN]->(c)
                    RETURN c
                """, country_properties)
    
    # Process Original Language
    if not pd.isna(row["orig_lang"]):
        languages = str(row["orig_lang"]).split(",")
        for language in languages:
            language = language.strip()
            if language:
                language_properties = {
                    "movie_id": movie_properties["movie_id"],
                    "language_name": language
                }
                
                graph.query("""
                    MATCH (m:Movie {id: $movie_id})
                    MERGE (l:Language {name: $language_name})
                    MERGE (m)-[:CREATED_IN]->(l)
                    RETURN l
                """, language_properties)
    
    # Process Genre
    if not pd.isna(row["genre"]):
        genres = str(row["genre"]).split(",")
        for genre in genres:
            # Clean genre name by removing special characters
            genre = clean_text(genre)
            if genre:
                genre_properties = {
                    "movie_id": movie_properties["movie_id"],
                    "genre_name": genre
                }
                
                graph.query("""
                    MATCH (m:Movie {id: $movie_id})
                    MERGE (g:Genre {name: $genre_name})
                    MERGE (m)-[:OF_GENRE]->(g)
                    RETURN g
                """, genre_properties)
    
    # Process Crew
    if not pd.isna(row["crew"]):
        crew_members = str(row["crew"]).split(",")
        for crew_member in crew_members:
            crew_member = crew_member.strip()
            if crew_member:
                crew_properties = {
                    "movie_id": movie_properties["movie_id"],
                    "crew_name": crew_member
                }
                
                graph.query("""
                    MATCH (m:Movie {id: $movie_id})
                    MERGE (c:Crew {name: $crew_name})
                    MERGE (c)-[:ACTED_IN]->(m)
                    RETURN c
                """, crew_properties)

print("Data import complete!")