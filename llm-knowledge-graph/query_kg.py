import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain.prompts import PromptTemplate
from typing import Dict, List, Any, Optional, Set, Tuple
import re

load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    openai_api_key=os.getenv('OPENAI_API_KEY'), 
    temperature=0,
    model="gpt-4"  # Using a more capable model for better context understanding
)

# Initialize the graph connection
graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# ---------- MEMORY COMPONENT PATTERN IMPLEMENTATION ---------- #

class ConversationMemory:
    """Stores the conversation history"""
    
    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.turns = []
    
    def add_turn(self, user_message: str, ai_message: str):
        """Add a new conversation turn"""
        self.turns.append({"user": user_message, "ai": ai_message})
        # Keep only the most recent interactions
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
    
    def get_formatted_history(self) -> str:
        """Get the conversation history as a formatted string"""
        if not self.turns:
            return ""
        
        formatted = []
        for turn in self.turns:
            formatted.append(f"Human: {turn['user']}")
            formatted.append(f"AI: {turn['ai']}")
        
        return "\n".join(formatted)
    
    def clear(self):
        """Clear the conversation history"""
        self.turns = []


class Entity:
    """Represents a tracked entity in the conversation"""
    
    def __init__(self, name: str, entity_type: str, confidence: float = 1.0):
        self.name = name
        self.entity_type = entity_type
        self.confidence = confidence
        self.attributes = {}
        self.aliases = set([name.lower()])
        self.first_mentioned_turn = None
        self.last_mentioned_turn = None
        self.mention_count = 1
    
    def add_alias(self, alias: str):
        """Add an alternative name for this entity"""
        if alias and alias.lower() not in self.aliases:
            self.aliases.add(alias.lower())
    
    def update_mention(self, turn_index: int):
        """Update when this entity was mentioned"""
        if self.first_mentioned_turn is None:
            self.first_mentioned_turn = turn_index
        self.last_mentioned_turn = turn_index
        self.mention_count += 1
    
    def add_attribute(self, key: str, value: Any):
        """Add or update an attribute for this entity"""
        self.attributes[key] = value
    
    def matches(self, text: str) -> bool:
        """Check if the given text matches any of this entity's names"""
        return text.lower() in self.aliases
    
    def __str__(self) -> str:
        return f"{self.name} ({self.entity_type})"


class EntityMemory:
    """Tracks entities mentioned in the conversation"""
    
    def __init__(self):
        self.entities = {}  # id -> Entity
        self.entities_by_type = {}  # type -> {id}
        self.current_entities = {}  # type -> id of most recently mentioned entity
        self.turn_index = 0
    
    def add_entity(self, name: str, entity_type: str) -> str:
        """Add a new entity and return its ID"""
        entity_id = f"{entity_type}:{name}".lower()
        
        if entity_id in self.entities:
            # Entity already exists, update it
            self.entities[entity_id].update_mention(self.turn_index)
        else:
            # Create new entity
            entity = Entity(name, entity_type)
            entity.update_mention(self.turn_index)
            self.entities[entity_id] = entity
            
            # Update entities by type
            if entity_type not in self.entities_by_type:
                self.entities_by_type[entity_type] = set()
            self.entities_by_type[entity_type].add(entity_id)
        
        # Update current entity of this type
        self.current_entities[entity_type] = entity_id
        
        return entity_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by its ID"""
        return self.entities.get(entity_id)
    
    def get_current_entity(self, entity_type: str) -> Optional[Entity]:
        """Get the most recently mentioned entity of a specific type"""
        entity_id = self.current_entities.get(entity_type)
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def find_entity_by_name(self, name: str, entity_type: Optional[str] = None) -> Optional[Entity]:
        """Find an entity by name, optionally filtering by type"""
        name_lower = name.lower()
        
        # If entity type is specified, only search entities of that type
        if entity_type and entity_type in self.entities_by_type:
            for entity_id in self.entities_by_type[entity_type]:
                entity = self.entities[entity_id]
                if entity.matches(name_lower):
                    return entity
        else:
            # Search all entities
            for entity in self.entities.values():
                if entity.matches(name_lower):
                    return entity
        
        return None
    
    def update_turn(self):
        """Update the current turn index"""
        self.turn_index += 1
    
    def clear(self):
        """Clear all entity data"""
        self.entities = {}
        self.entities_by_type = {}
        self.current_entities = {}
        self.turn_index = 0
    
    def get_formatted_context(self) -> str:
        """Get the entity context as a formatted string"""
        if not self.entities:
            return ""
        
        context_parts = []
        
        # Group entities by type
        for entity_type, entity_ids in self.entities_by_type.items():
            entities_of_type = [self.entities[eid] for eid in entity_ids]
            # Sort by most recently mentioned
            entities_of_type.sort(key=lambda e: (e.last_mentioned_turn or 0), reverse=True)
            
            # Format entities of this type
            entity_names = [e.name for e in entities_of_type]
            current_id = self.current_entities.get(entity_type)
            
            if current_id and current_id in self.entities:
                current_entity = self.entities[current_id]
                context_parts.append(f"Current {entity_type}: {current_entity.name}")
                
                # Add attributes for the current entity if available
                if current_entity.attributes:
                    for key, value in current_entity.attributes.items():
                        if isinstance(value, list):
                            value_str = ", ".join(str(v) for v in value)
                            context_parts.append(f"  {key}: {value_str}")
                        else:
                            context_parts.append(f"  {key}: {value}")
            
            context_parts.append(f"All {entity_type}s: {', '.join(entity_names)}")
        
        return "\n".join(context_parts)


class PronounResolver:
    """Resolves pronouns to their referent entities"""
    
    def __init__(self, entity_memory: EntityMemory):
        self.entity_memory = entity_memory
        
        # Define pronouns and their likely entity types
        self.pronoun_mappings = {
            "he": "Person",
            "him": "Person",
            "his": "Person",
            "she": "Person",
            "her": "Person",
            "hers": "Person",
            "they": None,  # Could be any type
            "them": None,
            "their": None,
            "it": None,  # Could be object, location, etc.
            "its": None
        }
    
    def resolve_pronouns(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replace pronouns with their referents and return the resolved text
        along with a mapping of what was replaced
        """
        resolved_text = text
        replacements = {}
        
        # Find all pronouns in the text
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if word in self.pronoun_mappings:
                entity_type = self.pronoun_mappings[word]
                referent = None
                
                # Try to find the referent entity
                if entity_type:
                    # If we know the entity type, get the most recent entity of that type
                    entity = self.entity_memory.get_current_entity(entity_type)
                    if entity:
                        referent = entity.name
                else:
                    # If we don't know the entity type, try to get the most recently mentioned entity
                    for type_name, entity_id in self.entity_memory.current_entities.items():
                        entity = self.entity_memory.get_entity(entity_id)
                        if entity and entity.last_mentioned_turn == self.entity_memory.turn_index - 1:
                            referent = entity.name
                            break
                
                # Replace the pronoun if we found a referent
                if referent:
                    # Use regex to ensure we match the pronoun as a whole word
                    pattern = r'\b' + re.escape(word) + r'\b'
                    resolved_text = re.sub(pattern, referent, resolved_text, flags=re.IGNORECASE)
                    replacements[word] = referent
        
        return resolved_text, replacements


class QueryProcessor:
    """Processes and enhances user queries based on conversation context"""
    
    def __init__(self, conversation_memory: ConversationMemory, entity_memory: EntityMemory):
        self.conversation_memory = conversation_memory
        self.entity_memory = entity_memory
        self.pronoun_resolver = PronounResolver(entity_memory)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and extract/resolve context
        Returns a dict with the processed query and context information
        """
        # Update entity memory turn counter
        self.entity_memory.update_turn()
        
        # Step 1: Resolve pronouns
        resolved_query, pronoun_replacements = self.pronoun_resolver.resolve_pronouns(query)
        
        # Step 2: Extract entities from the query
        extracted_entities = self._extract_entities_from_query(resolved_query)
        
        # Step 3: Update entity memory with extracted entities
        for entity_name, entity_type in extracted_entities:
            self.entity_memory.add_entity(entity_name, entity_type)
        
        # Return the processed information
        return {
            "original_query": query,
            "resolved_query": resolved_query,
            "pronoun_replacements": pronoun_replacements,
            "extracted_entities": extracted_entities
        }
    
    def _extract_entities_from_query(self, query: str) -> List[Tuple[str, str]]:
        """Extract entities from the query text"""
        entities = []
        
        # Simple extraction of person entities (could be enhanced with NER)
        if "for " in query.lower():
            person_name = query.split("for ")[-1].strip("?. ")
            entities.append((person_name, "Person"))
        
        # Extract body parts
        body_parts = [
            "hip", "knee", "shoulder", "ankle", "elbow", "wrist", "neck", "back", 
            "chest", "groin", "foot", "hand", "head", "rib", "leg", "arm"
        ]
        
        for part in body_parts:
            if part.lower() in query.lower():
                entities.append((part.capitalize(), "BodyPart"))
        
        return entities
    
    def extract_results(self, results: Any) -> List[Dict[str, Any]]:
        """
        Extract entities and relationships from query results and update entity memory
        """
        extracted_data = []
        
        # Handle common result structure
        if isinstance(results, dict) and 'context' in results:
            context_items = results['context']
            if isinstance(context_items, list):
                for item in context_items:
                    if isinstance(item, dict):
                        # Process each result item
                        processed_item = self._process_result_item(item)
                        if processed_item:
                            extracted_data.append(processed_item)
        
        return extracted_data
    
    def _process_result_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single result item and update entity memory"""
        processed = {}
        
        # Extract person information
        person_name = None
        for key in ['p.name', 'person.name', 'name']:
            if key in item and item[key]:
                person_name = item[key]
                processed['person'] = person_name
                # Update entity memory
                person_id = self.entity_memory.add_entity(person_name, "Person")
                break
        
        # Extract body part information
        body_part = None
        for key in ['bodyPart', 'b.name', 'body_part']:
            if key in item and item[key]:
                body_part = item[key]
                processed['body_part'] = body_part
                # Update entity memory
                body_part_id = self.entity_memory.add_entity(body_part, "BodyPart")
                
                # Link body part to person if both are present
                if person_name:
                    person = self.entity_memory.find_entity_by_name(person_name, "Person")
                    if person:
                        # Add body parts as an attribute of the person
                        if 'body_parts' not in person.attributes:
                            person.attributes['body_parts'] = []
                        if body_part not in person.attributes['body_parts']:
                            person.attributes['body_parts'].append(body_part)
                break
        
        # Extract other information (diagnosis, injury, etc.)
        for key, value in item.items():
            if value and key not in ['p.name', 'person.name', 'name', 'bodyPart', 'b.name', 'body_part']:
                processed[key] = value
        
        return processed if processed else None


class MemoryManager:
    """Manages all memory components"""
    
    def __init__(self):
        self.conversation_memory = ConversationMemory()
        self.entity_memory = EntityMemory()
        self.query_processor = QueryProcessor(self.conversation_memory, self.entity_memory)
    
    def process_user_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through all memory components"""
        return self.query_processor.process_query(query)
    
    def update_from_results(self, results: Any):
        """Update memory components from query results"""
        extracted_data = self.query_processor.extract_results(results)
        return extracted_data
    
    def add_interaction(self, user_query: str, ai_response: str):
        """Add a complete interaction to the conversation memory"""
        self.conversation_memory.add_turn(user_query, ai_response)
    
    def get_context_for_prompt(self) -> Dict[str, str]:
        """Get formatted context for prompts"""
        return {
            "conversation_history": self.conversation_memory.get_formatted_history(),
            "entity_context": self.entity_memory.get_formatted_context()
        }
    
    def clear(self):
        """Clear all memory components"""
        self.conversation_memory.clear()
        self.entity_memory.clear()

# Initialize the memory manager
memory_manager = MemoryManager()

# ---------- KNOWLEDGE GRAPH QA SYSTEM ---------- #

# Improved Cypher generation template with context
CYPHER_GENERATION_TEMPLATE = """Task: Generate a Cypher statement to query a graph database in a conversational context.

Current conversation history:
{conversation_history}

Current entity context:
{entity_context}

Instructions:
1. Use only the provided relationship types and properties in the schema.
2. Always use case-insensitive pattern matching with '(?i)' for string comparisons.
3. For names or identifiers, use partial matching with '.*name.*' pattern when appropriate.
4. Consider multiple potential paths to the answer to increase chances of finding relevant information.
5. Try multiple relationship patterns if you're not sure which one is used in the schema.
6. Always use OPTIONAL MATCH when possible to return partial results even if some parts of the pattern don't match.
7. Only include the generated Cypher statement in your response.
8. For questions about injuries, look for relationships like HAS_INJURY, HAD_INJURY, or any relationships to BodyPart nodes.
9. When searching for a person with a name like "{person_name}", use a case-insensitive match.
10. The original question "{original_query}" has been processed to "{resolved_query}" by resolving pronouns.

Schema:
{schema}

Examples:
# Find injuries for a person
MATCH (p:Person)
WHERE p.name =~ '(?i).*{person_name}.*' OR p.id =~ '(?i).*{person_name}.*'
MATCH (p)-[:HAD_INJURY]->(i:Injury)-[:LOCATED_IN]->(b:BodyPart)
RETURN p.name, b.name as bodyPart

# Find information about surgery for a person
MATCH (p:Person)
WHERE p.name =~ '(?i).*{person_name}.*' OR p.id =~ '(?i).*{person_name}.*'
OPTIONAL MATCH (p)-[:HAD_SURGERY]->(s:Surgery)
OPTIONAL MATCH (p)-[:HAD_INJURY]->(i:Injury)-[:HAD_SURGERY]->(s2:Surgery)
RETURN p.name, s.name as surgery, s2.name as injury_surgery, 
       CASE WHEN s IS NULL AND s2 IS NULL THEN false ELSE true END as had_surgery

# Find diagnosis for a specific body part injury
MATCH (p:Person)
WHERE p.name =~ '(?i).*{person_name}.*' OR p.id =~ '(?i).*{person_name}.*'
MATCH (p)-[:HAD_INJURY]->(i:Injury)-[:LOCATED_IN]->(b:BodyPart)
WHERE b.name =~ '(?i).*{body_part}.*'
OPTIONAL MATCH (i)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
RETURN p.name, b.name as bodyPart, d.name as diagnosis, d.details

The question is:
{resolved_query}"""

# QA template with more context
QA_TEMPLATE = """You are an assistant that helps users query information from a knowledge graph.

Current conversation history:
{conversation_history}

Current entity context:
{entity_context}

Context from the knowledge graph:
{context}

Original question: {original_query}
Resolved question (with pronouns replaced): {resolved_query}

Instructions:
1. Answer based ONLY on the information provided in the context.
2. Even if the context seems minimal (like a list of values), use that information to formulate a proper answer.
3. If the context doesn't contain ANY relevant information, say "I don't have information about that specific aspect in my knowledge graph."
4. Be concise and direct in your answer.
5. Use the names of people and entities as they appear in the entity context.
6. IMPORTANT: If the context contains any data at all that answers the question, you MUST provide an answer using that data rather than claiming you don't have enough information.

Answer:"""

def create_chain_with_context(query_info, debug_mode=False):
    """Create a chain with current context"""
    # Get context from memory manager
    context = memory_manager.get_context_for_prompt()
    conversation_history = context["conversation_history"]
    entity_context = context["entity_context"]
    
    # Extract relevant entity information
    person_name = ""
    body_part = ""
    
    # Get the current person if available
    current_person = memory_manager.entity_memory.get_current_entity("Person")
    if current_person:
        person_name = current_person.name
    
    # Get the current body part if available
    current_body_part = memory_manager.entity_memory.get_current_entity("BodyPart")
    if current_body_part:
        body_part = current_body_part.name
    
    # Extract entities from the query processing
    for entity_name, entity_type in query_info.get("extracted_entities", []):
        if entity_type == "Person":
            person_name = entity_name
        elif entity_type == "BodyPart":
            body_part = entity_name
    
    # Create the Cypher generation prompt
    cypher_prompt = PromptTemplate(
        template=CYPHER_GENERATION_TEMPLATE,
        input_variables=["schema", "resolved_query"],
        partial_variables={
            "conversation_history": conversation_history,
            "entity_context": entity_context,
            "person_name": person_name,
            "body_part": body_part,
            "original_query": query_info.get("original_query", ""),
            "resolved_query": query_info.get("resolved_query", query_info.get("original_query", ""))
        }
    )
    
    # Create the QA prompt
    qa_prompt = PromptTemplate(
        template=QA_TEMPLATE,
        input_variables=["context", "resolved_query"],
        partial_variables={
            "conversation_history": conversation_history,
            "entity_context": entity_context,
            "original_query": query_info.get("original_query", ""),
            "resolved_query": query_info.get("resolved_query", query_info.get("original_query", ""))
        }
    )
    
    # Create the chain
    chain = GraphCypherQAChain.from_llm(
        llm,
        graph=graph,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
        verbose=debug_mode,
        enhanced_schema=True,
        return_intermediate_steps=True,
        return_direct=False,
        allow_dangerous_requests=True
    )
    
    return chain

def process_results(query_info, result):
    """Process the results from the chain"""
    # Extract intermediate steps
    intermediate_steps = result.get("intermediate_steps", [])
    if len(intermediate_steps) < 2:
        return result.get("result", "❌ No answer found.")
    
    # Get the raw results
    raw_results = intermediate_steps[1]
    
    # Update memory from results
    if raw_results:
        memory_manager.update_from_results(raw_results)
    
    # Get the answer from the chain
    answer = result.get("result", "❌ No answer found.")
    
    # If the answer claims no information but we have results, provide a custom answer
    if "don't have information" in answer or "I don't have information" in answer:
        # Custom handling for specific queries about surgery
        if "surgery" in query_info.get("original_query", "").lower():
            # Check if we have surgery information
            for item in memory_manager.query_processor.extract_results(raw_results):
                if "surgery" in item or "had_surgery" in item:
                    person = memory_manager.entity_memory.get_current_entity("Person")
                    person_name = person.name if person else "The person"
                    
                    if item.get("had_surgery") == False or item.get("surgery") == None:
                        return f"No, {person_name} did not go through surgery."
                    else:
                        return f"Yes, {person_name} went through surgery: {item.get('surgery', 'unspecified surgery')}."
    
    return answer

def run_query(q, debug_mode=False):
    """Run a query through the knowledge graph QA system"""
    try:
        # Process the query through memory components
        query_info = memory_manager.process_user_query(q)
        
        if debug_mode:
            print("\n----- QUERY PROCESSING -----")
            print(f"Original: {query_info['original_query']}")
            print(f"Resolved: {query_info['resolved_query']}")
            print(f"Pronouns: {query_info['pronoun_replacements']}")
            print(f"Entities: {query_info['extracted_entities']}")
            print("----- END QUERY PROCESSING -----\n")
        
        # Create a chain with the current context
        chain = create_chain_with_context(query_info, debug_mode=debug_mode)
        
        # Use the resolved query for the chain
        query_to_use = query_info.get("resolved_query", q)
        
        # Run the query
        result = chain.invoke({"query": query_to_use})
        
        # Debug info
        if debug_mode:
            print("\n----- DEBUG INFO -----")
            intermediate_steps = result.get("intermediate_steps", [])
            if len(intermediate_steps) >= 2:
                print("Cypher query:", intermediate_steps[0].get("query", "No query"))
                raw_results = intermediate_steps[1]
                print("Raw results type:", type(raw_results))
                print("Raw results:", raw_results)
            print("Current entity context:", memory_manager.entity_memory.get_formatted_context())
            print("----- END DEBUG -----\n")
        
        # Process results
        answer = process_results(query_info, result)
        
        # Add to conversation memory
        memory_manager.add_interaction(q, answer)
        
        return answer
    except Exception as e:
        if debug_mode:
            print(f"Error in run_query: {str(e)}")
            import traceback
            traceback.print_exc()
        return f"⚠️ Error: {str(e)}"

# Main loop
print("Knowledge Graph Assistant - Type 'exit' to quit")
print("Type 'debug on' to enable verbose debugging or 'debug off' to disable it")
print("Type 'reset' to clear conversation context")
print("Type 'context' to show current conversation context")

# Debug mode
debug_mode = False

while True:
    q = input("> ")
    
    if q.lower() == "exit":
        break
    elif q.lower() == "debug on":
        debug_mode = True
        print("Debug mode enabled")
        continue
    elif q.lower() == "debug off":
        debug_mode = False
        print("Debug mode disabled")
        continue
    elif q.lower() == "reset":
        memory_manager.clear()
        print("Conversation context has been reset")
        continue
    elif q.lower() == "context":
        context = memory_manager.get_context_for_prompt()
        print("\nCurrent conversation context:")
        print(context["conversation_history"] or "[No conversation history]")
        print("\nCurrent entity context:")
        print(context["entity_context"] or "[No entity context]")
        continue
    
    # Run the query and get the answer
    answer = run_query(q, debug_mode=debug_mode)
    print(answer)