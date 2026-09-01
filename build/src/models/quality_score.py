"""QualityScore model encapsulating dimensional and overall document ratings."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class QualityScore:
    """Represents the multi-dimensional quality assessment of a document."""

    overallScore: float = 100.0
    writingScore: float = 100.0
    consistencyScore: float = 100.0
    formattingScore: float = 100.0
    readabilityScore: float = 100.0
    privacyScore: float = 100.0

    # Configurable category weights (summing to 1.0)
    writingWeight: float = 0.25
    consistencyWeight: float = 0.20
    formattingWeight: float = 0.20
    readabilityWeight: float = 0.20
    privacyWeight: float = 0.15

    def calculate(self) -> float:
        """Calculate weighted overall score based on current dimensional scores."""
        raw_overall = (
            (self.writingScore * self.writingWeight)
            + (self.consistencyScore * self.consistencyWeight)
            + (self.formattingScore * self.formattingWeight)
            + (self.readabilityScore * self.readabilityWeight)
            + (self.privacyScore * self.privacyWeight)
        )
        self.overallScore = round(max(0.0, min(100.0, raw_overall)), 1)
        return self.overallScore

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overallScore": round(self.overallScore, 1),
            "writingScore": round(self.writingScore, 1),
            "consistencyScore": round(self.consistencyScore, 1),
            "formattingScore": round(self.formattingScore, 1),
            "readabilityScore": round(self.readabilityScore, 1),
            "privacyScore": round(self.privacyScore, 1),
            "weights": {
                "writing": self.writingWeight,
                "consistency": self.consistencyWeight,
                "formatting": self.formattingWeight,
                "readability": self.readabilityWeight,
                "privacy": self.privacyWeight,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityScore":
        weights = data.get("weights", {})
        score = cls(
            overallScore=data.get("overallScore", 100.0),
            writingScore=data.get("writingScore", 100.0),
            consistencyScore=data.get("consistencyScore", 100.0),
            formattingScore=data.get("formattingScore", 100.0),
            readabilityScore=data.get("readabilityScore", 100.0),
            privacyScore=data.get("privacyScore", 100.0),
            writingWeight=weights.get("writing", 0.25),
            consistencyWeight=weights.get("consistency", 0.20),
            formattingWeight=weights.get("formatting", 0.20),
            readabilityWeight=weights.get("readability", 0.20),
            privacyWeight=weights.get("privacy", 0.15),
        )
        score.calculate()
        return score
