import unittest
from unittest.mock import MagicMock, patch
from cognitive.graph_memory import GraphMemory
from core.orchestrator_engine import OrchestratorEngine
from neo4j import GraphDatabase

class TestGraphIntegration(unittest.TestCase):
    
    @patch('cognitive.graph_memory.GraphDatabase')
    @patch('cognitive.graph_memory.LLMRouter')
    def test_graph_memory_indexing(self, MockRouter, MockGraphDB):
        # Mock Neo4j interactions
        mock_driver = MagicMock()
        mock_session = MagicMock()
        MockGraphDB.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock LLM extraction
        mock_router_instance = MockRouter.return_value
        mock_router_instance.chat.return_value.content = '{"nodes": [{"name": "Auth", "type": "Class"}], "edges": []}'

        gm = GraphMemory()
        
        # Test Indexing
        gm.index_content("test.py", "class Auth: pass")
        
        # Verify LLM was called
        mock_router_instance.chat.assert_called()
        
        # Verify Neo4j write
        mock_session.run.assert_called()

    @patch('cognitive.graph_memory.GraphDatabase')
    def test_graph_retrieval(self, MockGraphDB):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        MockGraphDB.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock query result
        mock_result = [
            {"n.name": "Auth", "type(r)": "USES", "m.name": "Redis", "n.type": "Class", "m.type": "Database"}
        ]
        mock_session.run.return_value = mock_result
        
        gm = GraphMemory()
        context = gm.retrieve_context("How does Auth work?")
        
        self.assertIn("(Class Auth) -[USES]-> (Database Redis)", context)

    @patch('core.orchestrator_engine.GraphMemory')
    @patch('core.orchestrator_engine.AgentSpawner')
    @patch('core.orchestrator_engine.AgentManager') 
    @patch('core.orchestrator_engine.SecurityValidator')
    def test_orchestrator_integration(self, MockSec, MockMgr, MockSpawn, MockGM):
        mock_gm_instance = MockGM.return_value
        mock_gm_instance.retrieve_context.return_value = "Graph Context: (A)-[REL]->(B)"
        
        # Mock other dependencies to avoid creating them
        MockSpawn.return_value = MagicMock()
        MockMgr.return_value = MagicMock()
        MockSec.return_value = MagicMock()

        engine = OrchestratorEngine()
        
        # Mock _plan and _execute_plan to bypass real execution logic
        engine._plan = MagicMock()
        engine._execute_plan = MagicMock(return_value={})
        engine._finalize = MagicMock(return_value="Final Report")
        engine._verify_and_heal = MagicMock(return_value=[])
        engine.file_manager = MagicMock() # Mock file manager
        engine.result_processor = MagicMock()

        engine.execute("Explain logic")
        
        # Verify Orchestrator called Graph Retrieval
        mock_gm_instance.retrieve_context.assert_called_with("Explain logic")

if __name__ == '__main__':
    unittest.main()
