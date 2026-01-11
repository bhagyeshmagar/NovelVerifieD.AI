"""
Constraint Types - Data structures for constraint-aware reasoning.

KDSH 2026 Track A:
This module defines the constraint types and data structures used for
multi-stage reasoning. Claims are decomposed into sub-claims, each
evaluated against specific constraint categories.

Constraint Categories:
- TEMPORAL: Events that must occur in a specific order
- CAPABILITY: Actions the character can/cannot perform
- COMMITMENT: Promises, oaths, relationships
- WORLD_RULE: Physical laws, magic systems, social structures
- PSYCHOLOGICAL: Beliefs, fears, motivations
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ConstraintType(Enum):
    """Categories of constraints for narrative reasoning."""
    TEMPORAL = "temporal"        # When events occur relative to each other
    CAPABILITY = "capability"    # What the character can/cannot do
    COMMITMENT = "commitment"    # Promises, oaths, loyalties
    WORLD_RULE = "world_rule"    # Laws of the narrative world
    PSYCHOLOGICAL = "psychological"  # Beliefs, fears, motivations
    FACTUAL = "factual"          # Concrete facts (names, places, relationships)


class Verdict(Enum):
    """Possible verdicts for claims and sub-claims."""
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNDETERMINED = "undetermined"


@dataclass
class SubClaim:
    """
    An atomic sub-claim extracted from the main claim.
    
    Sub-claims are the smallest unit of verification.
    Each represents a single fact or constraint that can be
    independently verified against the text.
    """
    id: str
    text: str
    constraint_type: ConstraintType
    parent_claim_id: str
    
    # Evidence tracking
    supporting_excerpts: List[str] = field(default_factory=list)
    contradicting_excerpts: List[str] = field(default_factory=list)
    
    # Reasoning
    verdict: Optional[Verdict] = None
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class ConstraintViolation:
    """
    A detected constraint violation.
    
    When evidence contradicts a sub-claim, a ConstraintViolation
    is created to document the specific conflict.
    """
    sub_claim_id: str
    constraint_type: ConstraintType
    description: str
    
    # The conflicting evidence
    novel_excerpt: str
    novel_position: str  # EARLY, MID, or LATE
    
    # Severity: how definitively this disproves the claim
    severity: str  # "DEFINITE", "LIKELY", "POSSIBLE"
    
    def to_dict(self) -> dict:
        return {
            "sub_claim_id": self.sub_claim_id,
            "constraint_type": self.constraint_type.value,
            "description": self.description,
            "novel_excerpt": self.novel_excerpt[:500],
            "novel_position": self.novel_position,
            "severity": self.severity
        }


@dataclass
class ClaimAnalysis:
    """
    Complete analysis of a claim through the multi-stage reasoning pipeline.
    
    This structure tracks:
    1. The original claim
    2. Decomposed sub-claims
    3. Evidence for/against each sub-claim
    4. Constraint violations detected
    5. Final synthesized verdict
    """
    claim_id: str
    claim_text: str
    character: str
    book_name: str
    
    # Decomposition stage output
    sub_claims: List[SubClaim] = field(default_factory=list)
    
    # Evidence aggregation stage output
    early_evidence: List[dict] = field(default_factory=list)
    mid_evidence: List[dict] = field(default_factory=list)
    late_evidence: List[dict] = field(default_factory=list)
    
    # Constraint evaluation stage output
    violations: List[ConstraintViolation] = field(default_factory=list)
    
    # Dual-perspective evaluation (anti-bias)
    support_score: float = 0.0
    contradiction_score: float = 0.0
    
    # Final synthesis
    verdict: Verdict = Verdict.UNDETERMINED
    confidence: float = 0.0
    reasoning: str = ""
    
    def has_definite_violation(self) -> bool:
        """Check if any DEFINITE constraint violation exists."""
        return any(v.severity == "DEFINITE" for v in self.violations)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "character": self.character,
            "book_name": self.book_name,
            "sub_claims": [
                {
                    "id": sc.id,
                    "text": sc.text,
                    "type": sc.constraint_type.value,
                    "verdict": sc.verdict.value if sc.verdict else None,
                    "confidence": sc.confidence,
                    "supporting_excerpts": sc.supporting_excerpts[:3],
                    "contradicting_excerpts": sc.contradicting_excerpts[:3],
                }
                for sc in self.sub_claims
            ],
            "temporal_evidence": {
                "early": len(self.early_evidence),
                "mid": len(self.mid_evidence),
                "late": len(self.late_evidence)
            },
            "violations": [v.to_dict() for v in self.violations],
            "support_score": self.support_score,
            "contradiction_score": self.contradiction_score,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


# ============================================================================
# Prompt Templates for Multi-Stage Reasoning
# ============================================================================

DECOMPOSITION_PROMPT = """Decompose this character backstory claim into atomic sub-claims.

CLAIM: "{claim_text}"
CHARACTER: "{character}"
BOOK: "{book_name}"

For each sub-claim, identify its constraint type:
- TEMPORAL: When events occur (before/after/during)
- CAPABILITY: What the character can/cannot do
- COMMITMENT: Promises, oaths, loyalties
- WORLD_RULE: Laws of the narrative world
- PSYCHOLOGICAL: Beliefs, fears, motivations
- FACTUAL: Concrete facts (names, places, relationships)

Output JSON array of sub-claims:
[
  {{"id": "SC1", "text": "...", "type": "temporal"}},
  {{"id": "SC2", "text": "...", "type": "factual"}}
]

Extract 2-5 sub-claims. Each should be independently verifiable."""


SUPPORT_SEEKING_PROMPT = """Find evidence that SUPPORTS this claim being TRUE.

CLAIM: "{claim_text}"
CHARACTER: "{character}"

EVIDENCE FROM NOVEL:
{evidence_text}

What specific passages confirm or are consistent with this claim?
Focus on:
- Direct statements matching the claim
- Events that would require the claim to be true
- Character knowledge/actions consistent with the claim

Output JSON:
{{
  "supporting_excerpts": ["quote1", "quote2"],
  "support_confidence": 0.0-1.0,
  "support_reasoning": "one sentence"
}}"""


CONTRADICTION_SEEKING_PROMPT = """Find evidence that CONTRADICTS this claim or makes it IMPOSSIBLE.

CLAIM: "{claim_text}"
CHARACTER: "{character}"

EVIDENCE FROM NOVEL:
{evidence_text}

What specific passages conflict with or disprove this claim?
Focus on:
- Direct contradictions
- Impossible timelines (events that can't both be true)
- Missing knowledge the character should have
- Actions incompatible with the claimed background

Output JSON:
{{
  "contradicting_excerpts": ["quote1", "quote2"],
  "contradiction_confidence": 0.0-1.0,
  "contradiction_reasoning": "one sentence",
  "violation_type": "temporal|capability|commitment|world_rule|factual|none"
}}"""


SYNTHESIS_PROMPT = """Synthesize a final verdict from the dual-perspective analysis.

CLAIM: "{claim_text}"

SUPPORT ANALYSIS:
- Confidence: {support_confidence}
- Reasoning: {support_reasoning}

CONTRADICTION ANALYSIS:
- Confidence: {contradiction_confidence}
- Reasoning: {contradiction_reasoning}
- Violation type: {violation_type}

SUB-CLAIM VERDICTS:
{sub_claim_verdicts}

DECISION RULES:
1. If ANY sub-claim has a DEFINITE contradiction → verdict = "contradicted"
2. If contradiction_confidence > 0.5 → verdict = "contradicted"
3. If support_confidence > 0.7 AND contradiction_confidence < 0.3 → verdict = "supported"
4. Otherwise → verdict = "undetermined"

Output JSON:
{{
  "verdict": "supported|contradicted|undetermined",
  "confidence": 0.0-1.0,
  "reasoning": "concise explanation citing specific evidence"
}}"""
