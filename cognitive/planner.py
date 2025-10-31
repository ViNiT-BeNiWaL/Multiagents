"""
Planner agent for breaking down complex tasks into subtasks
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ollama
import json


@dataclass
class SubTask:
    """Represents a subtask in a plan"""
    task_id: str
    description: str
    task_type: str  # coding, analysis, creative, etc.
    dependencies: List[str]
    estimated_complexity: str
    required_output: str


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task"""
    plan_id: str
    original_task: str
    subtasks: List[SubTask]
    execution_order: List[str]
    success_criteria: List[str]


class PlannerAgent:
    """Agent responsible for planning and task decomposition"""

    def __init__(self, model_name: str = "qwen2.5:14b", temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.plans: Dict[str, ExecutionPlan] = {}

    def create_plan(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create an execution plan for a task

        Args:
            task_description: Description of the task
            context: Additional context for planning

        Returns:
            ExecutionPlan with subtasks
        """
        # Build prompt for planning
        prompt = self._build_planning_prompt(task_description, context)

        # Get plan from LLM
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    'role': 'system',
                    'content': self._get_system_prompt()
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={'temperature': self.temperature}
        )

        # Parse response into plan
        plan = self._parse_plan_response(response['message']['content'], task_description)

        # Store plan
        self.plans[plan.plan_id] = plan

        return plan

    def refine_plan(self, plan_id: str, feedback: str) -> ExecutionPlan:
        """
        Refine an existing plan based on feedback

        Args:
            plan_id: ID of plan to refine
            feedback: Feedback for refinement

        Returns:
            Refined ExecutionPlan
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan {plan_id} not found")

        current_plan = self.plans[plan_id]

        prompt = f"""Refine this execution plan based on the feedback:

Original Task: {current_plan.original_task}

Current Plan:
{self._format_plan_for_prompt(current_plan)}

Feedback: {feedback}

Provide a refined plan that addresses the feedback."""

        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    'role': 'system',
                    'content': self._get_system_prompt()
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={'temperature': self.temperature}
        )

        refined_plan = self._parse_plan_response(
            response['message']['content'],
            current_plan.original_task
        )

        # Keep same plan_id but update content
        refined_plan.plan_id = plan_id
        self.plans[plan_id] = refined_plan

        return refined_plan

    def _get_system_prompt(self) -> str:
        """Get system prompt for planner"""
        return """You are an expert task planner. Your job is to break down complex tasks into clear, actionable subtasks.

For each plan, provide:
1. A list of subtasks with clear descriptions
2. The type of each task (coding, analysis, reasoning, math, creative, planning, general)
3. Dependencies between tasks
4. Execution order
5. Success criteria

Format your response as JSON with this structure:
{
    "subtasks": [
        {
            "id": "subtask_1",
            "description": "Clear description",
            "task_type": "coding|analysis|reasoning|math|creative|planning|general",
            "dependencies": ["subtask_id"],
            "complexity": "low|medium|high",
            "required_output": "What should be produced"
        }
    ],
    "execution_order": ["subtask_1", "subtask_2"],
    "success_criteria": ["Criterion 1", "Criterion 2"]
}"""

    def _build_planning_prompt(self, task_description: str, context: Optional[Dict[str, Any]]) -> str:
        """Build prompt for planning"""
        prompt = f"Create a detailed execution plan for this task:\n\n{task_description}"

        if context:
            prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"

        prompt += "\n\nProvide a comprehensive plan with clear subtasks."

        return prompt

    def _parse_plan_response(self, response: str, original_task: str) -> ExecutionPlan:
        """Parse LLM response into ExecutionPlan"""
        import time

        plan_id = f"plan_{int(time.time())}"

        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan_data = json.loads(json_str)
            else:
                # Fallback: parse from text
                plan_data = self._parse_text_plan(response)

            # Create SubTask objects
            subtasks = []
            for st in plan_data.get('subtasks', []):
                subtask = SubTask(
                    task_id=st['id'],
                    description=st['description'],
                    task_type=st.get('task_type', 'general'),
                    dependencies=st.get('dependencies', []),
                    estimated_complexity=st.get('complexity', 'medium'),
                    required_output=st.get('required_output', 'Task completion')
                )
                subtasks.append(subtask)

            execution_order = plan_data.get('execution_order', [st.task_id for st in subtasks])
            success_criteria = plan_data.get('success_criteria', ['All subtasks completed successfully'])

            return ExecutionPlan(
                plan_id=plan_id,
                original_task=original_task,
                subtasks=subtasks,
                execution_order=execution_order,
                success_criteria=success_criteria
            )

        except Exception as e:
            # Create a simple fallback plan
            return self._create_fallback_plan(plan_id, original_task)

    def _parse_text_plan(self, text: str) -> Dict[str, Any]:
        """Parse plan from plain text response"""
        # Simple text parsing fallback
        lines = text.strip().split('\n')
        subtasks = []

        task_count = 0
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                task_count += 1
                description = line.lstrip('0123456789.-* ')
                subtasks.append({
                    'id': f'subtask_{task_count}',
                    'description': description,
                    'task_type': 'general',
                    'dependencies': [],
                    'complexity': 'medium',
                    'required_output': 'Task completion'
                })

        return {
            'subtasks': subtasks,
            'execution_order': [st['id'] for st in subtasks],
            'success_criteria': ['All subtasks completed']
        }

    def _create_fallback_plan(self, plan_id: str, original_task: str) -> ExecutionPlan:
        """Create a simple fallback plan"""
        subtask = SubTask(
            task_id='subtask_1',
            description=original_task,
            task_type='general',
            dependencies=[],
            estimated_complexity='medium',
            required_output='Task completion'
        )

        return ExecutionPlan(
            plan_id=plan_id,
            original_task=original_task,
            subtasks=[subtask],
            execution_order=['subtask_1'],
            success_criteria=['Task completed successfully']
        )

    def _format_plan_for_prompt(self, plan: ExecutionPlan) -> str:
        """Format plan for inclusion in prompt"""
        output = []
        for subtask in plan.subtasks:
            output.append(f"- {subtask.task_id}: {subtask.description}")
            output.append(f"  Type: {subtask.task_type}")
            output.append(f"  Dependencies: {', '.join(subtask.dependencies) if subtask.dependencies else 'None'}")
        return '\n'.join(output)

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get a plan by ID"""
        return self.plans.get(plan_id)