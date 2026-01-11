
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent dir to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.orchestrator_engine import OrchestratorEngine
from cognitive.planner import ExecutionPlan, SubTask, PlannerAgent

class TestWebScraping(unittest.TestCase):
    @patch('core.orchestrator_engine.PlannerAgent.create_plan')
    @patch('action.web_scraper.requests.get')
    def test_scraping_flow(self, mock_get, mock_create_plan):
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Example Domain</h1><p>This domain is for use in illustrative examples in documents.</p></body></html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock the planner to return a scraping task
        mock_create_plan.return_value = ExecutionPlan(
            plan_id="test_plan",
            subtasks=[
                SubTask(
                    task_id="task_1",
                    description="Scrape the content of https://example.com",
                    task_type="web_scrape",
                    dependencies=[],
                    required_output="Scraped content"
                )
            ],
            execution_order=["task_1"]
        )

        # Initialize engine
        engine = OrchestratorEngine(workspace="./test_workspace")
        
        # Execute
        result = engine.execute("Fetch info from example.com")
        
        # Verify
        self.assertIn("task_1", result["results"])
        self.assertIn("Example Domain", result["results"]["task_1"])
        self.assertIn("This domain is for use", result["results"]["task_1"])
        print("Test passed: Web scraping task executed and content extracted.")

if __name__ == '__main__':
    unittest.main()
