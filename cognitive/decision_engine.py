"""
Decision engine for making intelligent choices during execution
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import ollama


class DecisionType(Enum):
    ROUTE = "route"  # Routing between options
    APPROVE = "approve"  # Approve/reject decision
    SELECT = "select"  # Select from multiple options
    PRIORITIZE = "prioritize"  # Prioritize items


@dataclass
class DecisionContext:
    """Context for making a decision"""
    decision_type: DecisionType
    question: str
    options: List[str]
    criteria: List[str]
    context_data: Dict[str, Any]


@dataclass
class Decision:
    """Result of a decision"""
    decision_id: str
    decision_type: DecisionType
    selected_option: str
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]]


class DecisionEngine:
    """Engine for making intelligent decisions"""

    def __init__(self, model_name: str = "gpt-oss:120b-cloud", temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature  # Lower temp for more consistent decisions
        self.decision_history: List[Decision] = []

    def make_decision(self, context: DecisionContext) -> Decision:
        """
        Make a decision based on context

        Args:
            context: DecisionContext with all relevant information

        Returns:
            Decision object with selection and reasoning
        """
        prompt = self._build_decision_prompt(context)

        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    'role': 'system',
                    'content': self._get_system_prompt(context.decision_type)
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={'temperature': self.temperature}
        )

        decision = self._parse_decision_response(
            response['message']['content'],
            context
        )

        self.decision_history.append(decision)
        return decision

    def route_task(self, task_description: str, available_agents: List[str]) -> Decision:
        """
        Route a task to the most appropriate agent

        Args:
            task_description: Description of the task
            available_agents: List of available agent IDs

        Returns:
            Decision on which agent to use
        """
        context = DecisionContext(
            decision_type=DecisionType.ROUTE,
            question=f"Which agent should handle this task: {task_description}",
            options=available_agents,
            criteria=["Agent capability", "Current load", "Task fit"],
            context_data={"task": task_description}
        )

        return self.make_decision(context)

    def approve_result(self, result: Any, quality_criteria: List[str]) -> Decision:
        """
        Approve or reject a result based on quality criteria

        Args:
            result: Result to evaluate
            quality_criteria: Criteria for approval

        Returns:
            Decision to approve or reject
        """
        context = DecisionContext(
            decision_type=DecisionType.APPROVE,
            question="Should this result be approved?",
            options=["approve", "reject", "revise"],
            criteria=quality_criteria,
            context_data={"result": str(result)}
        )

        return self.make_decision(context)

    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> Decision:
        """
        Prioritize a list of tasks

        Args:
            tasks: List of task dictionaries

        Returns:
            Decision with prioritized task order
        """
        task_ids = [task.get('id', f"task_{i}") for i, task in enumerate(tasks)]

        context = DecisionContext(
            decision_type=DecisionType.PRIORITIZE,
            question="In what order should these tasks be executed?",
            options=task_ids,
            criteria=["Dependencies", "Urgency", "Impact"],
            context_data={"tasks": tasks}
        )

        return self.make_decision(context)

    def _get_system_prompt(self, decision_type: DecisionType) -> str:
        """Get system prompt based on decision type"""
        base_prompt = "You are an expert decision-making system. Analyze the provided information carefully and make the best decision."

        type_specific = {
            DecisionType.ROUTE: "Focus on matching task requirements with agent capabilities.",
            DecisionType.APPROVE: "Evaluate the result against the quality criteria objectively.",
            DecisionType.SELECT: "Compare all options systematically and choose the best fit.",
            DecisionType.PRIORITIZE: "Consider dependencies, urgency, and impact when ordering."
        }

        return f"{base_prompt}\n\n{type_specific.get(decision_type, '')}\n\nProvide your decision in JSON format with: selected_option, confidence (0-1), reasoning, and alternatives."

    def _build_decision_prompt(self, context: DecisionContext) -> str:
        """Build prompt for decision making"""
        prompt_parts = [
            f"Decision Type: {context.decision_type.value}",
            f"\nQuestion: {context.question}",
            f"\nOptions:",
        ]

        for i, option in enumerate(context.options, 1):
            prompt_parts.append(f"  {i}. {option}")

        if context.criteria:
            prompt_parts.append(f"\nEvaluation Criteria:")
            for criterion in context.criteria:
                prompt_parts.append(f"  - {criterion}")

        if context.context_data:
            prompt_parts.append(f"\nAdditional Context:")
            for key, value in context.context_data.items():
                value_str = str(value)[:200]  # Truncate long values
                prompt_parts.append(f"  {key}: {value_str}")

        prompt_parts.append("\nProvide your decision with reasoning.")

        return "\n".join(prompt_parts)

    def _parse_decision_response(self, response: str, context: DecisionContext) -> Decision:
        """Parse LLM response into Decision object"""
        import json
        import time

        decision_id = f"decision_{int(time.time())}"

        try:
            # Try to extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                decision_data = json.loads(json_str)

                selected = decision_data.get('selected_option', context.options[0])
                confidence = float(decision_data.get('confidence', 0.7))
                reasoning = decision_data.get('reasoning', 'No reasoning provided')
                alternatives = decision_data.get('alternatives', [])
            else:
                # Fallback parsing
                selected = self._extract_selection_from_text(response, context.options)
                confidence = 0.6
                reasoning = response[:500]  # Use first part of response
                alternatives = []

            return Decision(
                decision_id=decision_id,
                decision_type=context.decision_type,
                selected_option=selected,
                confidence=confidence,
                reasoning=reasoning,
                alternatives=alternatives
            )

        except Exception as e:
            # Fallback decision
            return Decision(
                decision_id=decision_id,
                decision_type=context.decision_type,
                selected_option=context.options[0] if context.options else "default",
                confidence=0.5,
                reasoning=f"Fallback decision due to parsing error: {str(e)}",
                alternatives=[]
            )

    def _extract_selection_from_text(self, text: str, options: List[str]) -> str:
        """Extract selection from plain text response"""
        text_lower = text.lower()

        # Look for exact matches
        for option in options:
            if option.lower() in text_lower:
                return option

        # Look for numbered selections
        for i, option in enumerate(options, 1):
            if f"{i}." in text or f"option {i}" in text_lower:
                return option

        # Default to first option
        return options[0] if options else "default"

    def get_decision_history(self) -> List[Decision]:
        """Get history of all decisions made"""
        return self.decision_history.copy()

    def get_confidence_stats(self) -> Dict[str, float]:
        """Get statistics on decision confidence"""
        if not self.decision_history:
            return {"avg_confidence": 0.0, "min_confidence": 0.0, "max_confidence": 0.0}

        confidences = [d.confidence for d in self.decision_history]

        return {
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "total_decisions": len(confidences)
        }