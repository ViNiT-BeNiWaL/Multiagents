from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import json
from config.settings import settings
from core.llm_router import LLMRouter

class GraphMemory:
    """
    Manages the Knowledge Graph (Neo4j).
    Handles extraction of entities/relationships from text and retrieval for RAG.
    """
    
    def __init__(self):
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri, 
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self.driver.verify_connectivity()
            print(f"✓ Connected to Neo4j at {settings.neo4j_uri}")
        except Exception as e:
            print(f"⚠ Failed to connect to Neo4j: {e}")
            self.driver = None

        # Use a fast model for extraction to reduce latency
        self.router = LLMRouter(model="deepseek-v3.1:671b-cloud") 

    def close(self):
        if self.driver:
            self.driver.close()

    def index_content(self, file_path: str, content: str):
        """
        Extracts graph elements from content and indexes them in Neo4j.
        """
        if not self.driver:
            return

        # 1. Extract Nodes/Edges using LLM
        graph_data = self._extract_graph_from_text(file_path, content)
        
        # 2. Persist to Neo4j
        if graph_data:
            self._write_to_neo4j(graph_data)

    def retrieve_context(self, query: str) -> str:
        """
        Retrieves relevant graph context for a user query.
        """
        if not self.driver:
            return ""

        # Simple 2-hop traversal from recognized entities
        # For a full implementation, we'd extract entities from the query first.
        # Here we do a fuzzy search on nodes that match words in the query.
        
        keywords = [w for w in query.split() if len(w) > 4] # distinct words
        context_parts = []
        
        with self.driver.session() as session:
            for word in keywords:
                result = session.run(
                    """
                    MATCH (n)-[r]-(m) 
                    WHERE n.name CONTAINS $word 
                    RETURN n.name, type(r), m.name, n.type, m.type
                    LIMIT 5
                    """,
                    word=word
                )
                
                for record in result:
                    context_parts.append(
                        f"({record['n.type']} {record['n.name']}) -[{record['type(r)']}]-> ({record['m.type']} {record['m.name']})"
                    )
        
        if not context_parts:
            return ""
            
        return "Graph Context:\n" + "\n".join(list(set(context_parts)))

    def _extract_graph_from_text(self, file_path: str, content: str) -> Optional[Dict]:
        """
        Uses LLM to parse text into JSON graph representation.
        """
        system_prompt = (
            "You are a Knowledge Graph Extractor. "
            "Analyze the provided code/text and extract Entities (Nodes) and Relationships (Edges). "
            "Return JSON ONLY.\n\n"
            "Format:\n"
            "{\n"
            "  \"nodes\": [{\"name\": \"AuthManager\", \"type\": \"Class\", \"desc\": \"Handles login\"}],\n"
            "  \"edges\": [{\"source\": \"AuthManager\", \"target\": \"Redis\", \"type\": \"USES\"}]\n"
            "}"
        )
        
        # Truncate content to avoid token limits
        safe_content = content[:4000]
        
        try:
            response = self.router.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"File: {file_path}\n\n{safe_content}"}
                ],
                format="json",
                temperature=0.1
            )
            return json.loads(response.content)
        except Exception as e:
            print(f"Extraction failed for {file_path}: {e}")
            return None

    def _write_to_neo4j(self, data: Dict):
        """
        Writes nodes and edges to Neo4j database.
        """
        query = """
        UNWIND $nodes as node
        MERGE (n:Entity {name: node.name})
        SET n.type = node.type, n.desc = node.desc
        
        WITH n
        UNWIND $edges as edge
        MATCH (s:Entity {name: edge.source})
        MATCH (t:Entity {name: edge.target})
        MERGE (s)-[r:RELATIONSHIP {type: edge.type}]->(t)
        """
        
        # Dynamic relationship types is hard in param Cypher, 
        # so we normalize to generic 'RELATIONSHIP' with a type property for MVP stability,
        # OR we construct dynamic queries. Let's do dynamic queries for better visualization.
        
        with self.driver.session() as session:
            # 1. Create Nodes
            for node in data.get("nodes", []):
                session.run(
                    "MERGE (n:Entity {name: $name}) SET n.type = $type, n.desc = $desc",
                    name=node["name"], type=node.get("type", "Unknown"), desc=node.get("desc", "")
                )
                
            # 2. Create Edges
            for edge in data.get("edges", []):
                rel_type = edge.get("type", "RELATED_TO").upper().replace(" ", "_")
                # Sanitize rel_type to avoid injection (simple alpha check)
                if not rel_type.replace("_", "").isalnum():
                    rel_type = "RELATED_TO"
                
                cypher = (
                    f"MATCH (s:Entity {{name: $source}}) "
                    f"MATCH (t:Entity {{name: $target}}) "
                    f"MERGE (s)-[:{rel_type}]->(t)"
                )
                
                session.run(
                    cypher,
                    source=edge["source"],
                    target=edge["target"]
                )
