"""
Finalizer agent for reviewing and consolidating results
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import ollama


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    quality_score: float


@dataclass
class FinalReport:
    """Final consolidated report"""
    report_id: str
    original_task: str
    summary: str
    results: Dict[str, Any]
    validation: ValidationResult
    recommendations: List[str]
    metadata: Dict[str, Any]


class FinalizerAgent:
    """Agent responsible for final review and consolidation"""

    def __init__(self, model_name: str = "llama3.1:8b", temperature: float = 0.5):
        self.model_name = model_name
        self.temperature = temperature
        self.reports: Dict[str, FinalReport] = {}

    def validate_results(
            self,
            results: Dict[str, Any],
            criteria: List[str]
    ) -> ValidationResult:
        """
        Validate results against criteria

        Args:
            results: Results to validate
            criteria: Validation criteria

        Returns:
            ValidationResult with issues and suggestions
        """
        prompt = f"""Validate these results against the provided criteria:

Results:
{self._format_results(results)}

Validation Criteria:
{chr(10).join(f'- {c}' for c in criteria)}

Provide validation in JSON format with:
- is_valid: true/false
- issues: list of identified issues
- suggestions: list of improvement suggestions
- quality_score: 0-1 rating"""

        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a quality assurance expert. Validate results objectively and provide constructive feedback.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={'temperature': self.temperature}
        )

        return self._parse_validation_response(response['message']['content'])

    def consolidate_results(
            self,
            task_description: str,
            subtask_results: Dict[str, Any],
            validation_criteria: Optional[List[str]] = None
    ) -> FinalReport:
        """
        Consolidate multiple subtask results into final report

        Args:
            task_description: Original task description
            subtask_results: Results from all subtasks
            validation_criteria: Optional validation criteria

        Returns:
            FinalReport with consolidated information
        """
        import time

        # Validate results if criteria provided
        if validation_criteria:
            validation = self.validate_results(subtask_results, validation_criteria)
        else:
            validation = ValidationResult(
                is_valid=True,
                issues=[],
                suggestions=[],
                quality_score=0.8
            )

        # Generate summary
        summary = self._generate_summary(task_description, subtask_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(subtask_results, validation)

        # Create report
        report_id = f"report_{int(time.time())}"
        report = FinalReport(
            report_id=report_id,
            original_task=task_description,
            summary=summary,
            results=subtask_results,
            validation=validation,
            recommendations=recommendations,
            metadata={
                'subtask_count': len(subtask_results),
                'validation_score': validation.quality_score
            }
        )

        self.reports[report_id] = report
        return report

    def _generate_summary(
            self,
            task_description: str,
            results: Dict[str, Any]
    ) -> str:
        """Generate summary of results"""
        prompt = f"""Provide a concise summary of these task results:

Original Task: {task_description}

Results:
{self._format_results(results)}

Provide a clear, concise summary (2-4 sentences) of what was accomplished."""

        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an expert at summarizing technical work. Be concise and clear.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={'temperature': self.temperature}
        )

        return response['message']['content'].strip()

    def _generate_recommendations(
            self,
            results: Dict[str, Any],
            validation: ValidationResult
    ) -> List[str]:
        """Generate recommendations based on results and validation"""
        recommendations = []

        # Add suggestions from validation
        recommendations.extend(validation.suggestions)

        # Generate additional recommendations
        if validation.quality_score < 0.7:
            prompt = f"""Based on these results and validation, what recommendations would you make for improvement?

Results Summary:
{self._format_results(results, max_length=500)}

Validation Issues:
{chr(10).join(f'- {issue}' for issue in validation.issues)}

Provide 3-5 specific, actionable recommendations."""

            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Provide specific, actionable recommendations for improvement.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    options={'temperature': self.temperature}
                )

                # Parse recommendations from response
                content = response['message']['content']
                for line in content.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                        rec = line.lstrip('0123456789.-* ').strip()
                        if rec and rec not in recommendations:
                            recommendations.append(rec)
            except:
                pass

        return recommendations[:5]  # Limit to 5 recommendations

    def _format_results(self, results: Dict[str, Any], max_length: int = 1000) -> str:
        """Format results for prompt inclusion"""
        import json

        try:
            formatted = json.dumps(results, indent=2)
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "\n... (truncated)"
            return formatted
        except:
            return str(results)[:max_length]

    def _parse_validation_response(self, response: str) -> ValidationResult:
        """Parse validation response into ValidationResult"""
        import json

        try:
            # Try to extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                return ValidationResult(
                    is_valid=data.get('is_valid', True),
                    issues=data.get('issues', []),
                    suggestions=data.get('suggestions', []),
                    quality_score=float(data.get('quality_score', 0.7))
                )
        except:
            pass

        # Fallback parsing
        is_valid = 'valid' in response.lower() and 'not valid' not in response.lower()
        issues = self._extract_list_items(response, ['issue', 'problem', 'concern'])
        suggestions = self._extract_list_items(response, ['suggest', 'recommend', 'improve'])

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            suggestions=suggestions,
            quality_score=0.7 if is_valid else 0.5
        )

    def _extract_list_items(self, text: str, keywords: List[str]) -> List[str]:
        """Extract list items from text based on keywords"""
        items = []