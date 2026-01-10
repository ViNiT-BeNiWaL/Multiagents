from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ValidationResult:
    is_valid: bool
    quality_score: float
    issues: List[str]


@dataclass
class FinalReport:
    summary: str
    validation: ValidationResult


class FinalizerAgent:
    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature

    def consolidate_results(
        self,
        task: str,
        results: Dict[str, Any],
        validation_criteria: List[str]
    ) -> FinalReport:
        """
        Consolidate results and validate against criteria
        """

        # Simple deterministic validation (v1)
        issues = []

        for criterion in validation_criteria:
            if not results:
                issues.append(f"Failed criterion: {criterion}")

        quality_score = 1.0 if not issues else 0.7

        return FinalReport(
            summary=f"Task '{task}' completed successfully.",
            validation=ValidationResult(
                is_valid=len(issues) == 0,
                quality_score=quality_score,
                issues=issues
            )
        )
