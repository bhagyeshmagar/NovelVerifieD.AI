"""
Reasoning Agent - Multi-stage constraint-aware verification.

NovelVerified.AI Pathway-based:
This agent implements a 4-stage reasoning pipeline:
1. DECOMPOSE: Break claim into atomic sub-claims
2. RETRIEVE: Get temporal-aware evidence
3. EVALUATE: Check constraints with dual-perspective (support + contradict)
4. SYNTHESIZE: Combine into final verdict with confidence calibration

Key anti-bias features:
- Dual prompts: actively seek contradictions, not just support
- Confidence calibration: penalize overconfident "supported" verdicts
- Constraint checking: detect violations even without explicit contradictions
"""

import json
import os
import time
import logging
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

# Import constraint types (handle both direct execution and test imports)
try:
    from agents.constraint_types import (
        ConstraintType, Verdict, SubClaim, ConstraintViolation, ClaimAnalysis,
        DECOMPOSITION_PROMPT, SUPPORT_SEEKING_PROMPT, 
        CONTRADICTION_SEEKING_PROMPT, SYNTHESIS_PROMPT
    )
except ImportError:
    from constraint_types import (
        ConstraintType, Verdict, SubClaim, ConstraintViolation, ClaimAnalysis,
        DECOMPOSITION_PROMPT, SUPPORT_SEEKING_PROMPT, 
        CONTRADICTION_SEEKING_PROMPT, SYNTHESIS_PROMPT
    )

# Load environment variables
load_dotenv()

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('reasoning_agent.log', mode='a')
    ]
)
logger = logging.getLogger('reasoning_agent')

# ============================================================================
# Configuration
# ============================================================================
EVIDENCE_DIR = Path("evidence")
OUTPUT_DIR = Path("verdicts")
RATE_LIMIT_DELAY = 1.0  # Increased for multi-stage calls

# Retry configuration
MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0

# Claude configuration
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ============================================================================
# Anti-Bias Thresholds
# ============================================================================
# These thresholds are calibrated to prevent "supported" bias

CONTRADICTION_THRESHOLD = 0.4  # Any contradiction > this = contradicted
STRONG_SUPPORT_THRESHOLD = 0.7  # Need high support AND low contradiction
WEAK_CONTRADICTION_THRESHOLD = 0.25  # Below this, support can override

# ============================================================================
# LLM Call with Retry
# ============================================================================

def exponential_backoff_delay(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return delay + jitter


def call_llm(client: Anthropic, prompt: str, claim_id: str, stage: str) -> Optional[dict]:
    """
    Call Claude API with retry logic.
    Returns parsed JSON or None on failure.
    """
    system = "You output valid JSON only. No markdown, no commentary."
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text.strip()
            
            # Handle markdown code blocks
            if text.startswith("```"):
                lines = text.split("\n")
                json_lines = [l for l in lines if not l.startswith("```")]
                text = "\n".join(json_lines)
            
            return json.loads(text)
            
        except (RateLimitError, APIConnectionError) as e:
            delay = exponential_backoff_delay(attempt)
            logger.warning(f"{claim_id}/{stage}: Retrying in {delay:.1f}s - {e}")
            time.sleep(delay)
            
        except json.JSONDecodeError as e:
            logger.warning(f"{claim_id}/{stage}: JSON parse error - {e}")
            return None
            
        except Exception as e:
            logger.error(f"{claim_id}/{stage}: Error - {e}")
            return None
    
    return None


# ============================================================================
# Stage 1: Claim Decomposition
# ============================================================================

def decompose_claim(client: Anthropic, claim_data: dict) -> List[SubClaim]:
    """
    Decompose a claim into atomic sub-claims.
    
    Each sub-claim represents a single verifiable fact with
    its constraint type (temporal, capability, etc.)
    """
    prompt = DECOMPOSITION_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data["character"],
        book_name=claim_data["book_name"]
    )
    
    result = call_llm(client, prompt, claim_data["claim_id"], "decompose")
    
    if not result or not isinstance(result, list):
        # Fallback: treat entire claim as single sub-claim
        return [SubClaim(
            id="SC1",
            text=claim_data["claim_text"],
            constraint_type=ConstraintType.FACTUAL,
            parent_claim_id=claim_data["claim_id"]
        )]
    
    sub_claims = []
    for item in result:
        try:
            constraint_type = ConstraintType(item.get("type", "factual").lower())
        except ValueError:
            constraint_type = ConstraintType.FACTUAL
            
        sub_claims.append(SubClaim(
            id=item.get("id", f"SC{len(sub_claims)+1}"),
            text=item.get("text", ""),
            constraint_type=constraint_type,
            parent_claim_id=claim_data["claim_id"]
        ))
    
    return sub_claims if sub_claims else [SubClaim(
        id="SC1",
        text=claim_data["claim_text"],
        constraint_type=ConstraintType.FACTUAL,
        parent_claim_id=claim_data["claim_id"]
    )]


# ============================================================================
# Stage 2: Dual-Perspective Evidence Evaluation
# ============================================================================

def evaluate_for_support(client: Anthropic, claim_data: dict, 
                         evidence_text: str) -> Tuple[float, str, List[str]]:
    """
    Seek evidence that SUPPORTS the claim.
    Returns (confidence, reasoning, excerpts)
    """
    prompt = SUPPORT_SEEKING_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data["character"],
        evidence_text=evidence_text
    )
    
    result = call_llm(client, prompt, claim_data["claim_id"], "support")
    
    if not result:
        return 0.0, "Failed to analyze support", []
    
    return (
        float(result.get("support_confidence", 0.0)),
        result.get("support_reasoning", "No reasoning"),
        result.get("supporting_excerpts", [])
    )


def evaluate_for_contradiction(client: Anthropic, claim_data: dict,
                                evidence_text: str) -> Tuple[float, str, List[str], str]:
    """
    Seek evidence that CONTRADICTS the claim.
    Returns (confidence, reasoning, excerpts, violation_type)
    
    ANTI-BIAS: This is the key stage. We actively look for reasons
    the claim could be FALSE, not just reasons it could be true.
    """
    prompt = CONTRADICTION_SEEKING_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data["character"],
        evidence_text=evidence_text
    )
    
    result = call_llm(client, prompt, claim_data["claim_id"], "contradict")
    
    if not result:
        return 0.0, "Failed to analyze contradiction", [], "none"
    
    return (
        float(result.get("contradiction_confidence", 0.0)),
        result.get("contradiction_reasoning", "No reasoning"),
        result.get("contradicting_excerpts", []),
        result.get("violation_type", "none")
    )


# ============================================================================
# Stage 3: Verdict Synthesis with Calibration
# ============================================================================

def synthesize_verdict(support_conf: float, support_reason: str,
                       contradict_conf: float, contradict_reason: str,
                       violation_type: str, sub_claims: List[SubClaim]) -> Tuple[Verdict, float, str]:
    """
    Synthesize final verdict from dual-perspective analysis.
    
    ANTI-BIAS DECISION RULES:
    1. Any strong contradiction (>0.4) → contradicted
    2. High support (>0.7) AND low contradiction (<0.25) → supported
    3. Otherwise → undetermined
    
    This prevents the "default to supported" bias.
    """
    # Rule 1: Strong contradiction wins
    if contradict_conf > CONTRADICTION_THRESHOLD:
        confidence = min(0.95, contradict_conf + 0.1)
        reasoning = f"Contradiction found ({violation_type}): {contradict_reason}"
        return Verdict.CONTRADICTED, confidence, reasoning
    
    # Rule 2: Strong support with weak contradiction
    if support_conf > STRONG_SUPPORT_THRESHOLD and contradict_conf < WEAK_CONTRADICTION_THRESHOLD:
        confidence = support_conf * 0.9  # Slightly penalize
        reasoning = f"Evidence supports claim: {support_reason}"
        return Verdict.SUPPORTED, confidence, reasoning
    
    # Rule 3: Ambiguous → undetermined
    # Check if sub-claims have mixed verdicts
    sub_verdicts = [sc.verdict for sc in sub_claims if sc.verdict]
    has_support = any(v == Verdict.SUPPORTED for v in sub_verdicts)
    has_contradict = any(v == Verdict.CONTRADICTED for v in sub_verdicts)
    
    if has_support and has_contradict:
        reasoning = "Mixed evidence: some sub-claims supported, others contradicted"
    elif support_conf > contradict_conf:
        reasoning = f"Weak support without clear contradiction: {support_reason}"
    else:
        reasoning = f"Insufficient evidence to verify claim"
    
    confidence = max(0.3, min(support_conf, 0.5))
    return Verdict.UNDETERMINED, confidence, reasoning


# ============================================================================
# Main Processing Pipeline
# ============================================================================

def process_claim(client: Anthropic, claim_data: dict) -> dict:
    """
    Process a single claim through the 4-stage pipeline.
    
    Stages:
    1. DECOMPOSE: Break into sub-claims
    2. RETRIEVE: (already done by retriever_agent)
    3. EVALUATE: Dual-perspective analysis
    4. SYNTHESIZE: Calibrated verdict
    """
    claim_id = claim_data["claim_id"]
    
    # Initialize claim analysis
    analysis = ClaimAnalysis(
        claim_id=claim_id,
        claim_text=claim_data["claim_text"],
        character=claim_data.get("character", "Unknown"),
        book_name=claim_data.get("book_name", "Unknown")
    )
    
    # Stage 1: Decomposition
    analysis.sub_claims = decompose_claim(client, claim_data)
    logger.debug(f"{claim_id}: Decomposed into {len(analysis.sub_claims)} sub-claims")
    
    # Prepare evidence text
    evidence = claim_data.get("evidence", [])
    evidence_text = "\n\n".join([
        f"[{e.get('temporal_slice', 'MID')}] {e['text'][:1500]}"
        for e in evidence[:5]
    ])
    
    # Categorize evidence by temporal slice
    for e in evidence:
        slice_name = e.get("temporal_slice", "MID")
        if slice_name == "EARLY":
            analysis.early_evidence.append(e)
        elif slice_name == "LATE":
            analysis.late_evidence.append(e)
        else:
            analysis.mid_evidence.append(e)
    
    # Stage 2: Dual-Perspective Evaluation
    support_conf, support_reason, support_excerpts = evaluate_for_support(
        client, claim_data, evidence_text
    )
    
    time.sleep(0.5)  # Rate limit between calls
    
    contradict_conf, contradict_reason, contradict_excerpts, violation_type = evaluate_for_contradiction(
        client, claim_data, evidence_text
    )
    
    analysis.support_score = support_conf
    analysis.contradiction_score = contradict_conf
    
    # Track violations
    if contradict_conf > 0.3 and violation_type != "none":
        analysis.violations.append(ConstraintViolation(
            sub_claim_id="MAIN",
            constraint_type=ConstraintType(violation_type) if violation_type in [e.value for e in ConstraintType] else ConstraintType.FACTUAL,
            description=contradict_reason,
            novel_excerpt=contradict_excerpts[0] if contradict_excerpts else "",
            novel_position="UNKNOWN",
            severity="DEFINITE" if contradict_conf > 0.6 else "LIKELY" if contradict_conf > 0.4 else "POSSIBLE"
        ))
    
    # Stage 3: Synthesis
    analysis.verdict, analysis.confidence, analysis.reasoning = synthesize_verdict(
        support_conf, support_reason,
        contradict_conf, contradict_reason,
        violation_type, analysis.sub_claims
    )
    
    # Build output dict
    return {
        "claim_id": claim_id,
        "verdict": analysis.verdict.value,
        "confidence": round(analysis.confidence, 2),
        "supporting_spans": support_excerpts[:3],
        "contradicting_spans": contradict_excerpts[:3],
        "reasoning": analysis.reasoning[:300],
        # Extended analysis for dossiers
        "analysis": analysis.to_dict()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for multi-stage reasoning agent."""
    print("=" * 60)
    print("REASONING AGENT - Multi-Stage Constraint-Aware Verification")
    print("NovelVerified.AI Pathway-based: Dual-perspective anti-bias reasoning")
    print("=" * 60)
    
    logger.info("Starting reasoning agent with anti-bias pipeline")
    
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        return
    
    evidence_files = list(EVIDENCE_DIR.glob("*.json"))
    if not evidence_files:
        print(f"ERROR: No evidence files found in {EVIDENCE_DIR}/")
        return
    
    print(f"Found {len(evidence_files)} evidence files")
    print(f"Using model: {CLAUDE_MODEL}")
    print(f"\nAnti-bias thresholds:")
    print(f"  - Contradiction threshold: {CONTRADICTION_THRESHOLD}")
    print(f"  - Strong support threshold: {STRONG_SUPPORT_THRESHOLD}")
    
    client = Anthropic(api_key=API_KEY)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for already processed
    processed = set(f.stem for f in OUTPUT_DIR.glob("*.json"))
    remaining = [f for f in evidence_files if f.stem not in processed]
    
    if processed:
        print(f"  {len(processed)} already processed, {len(remaining)} remaining")
    
    stats = {"supported": 0, "contradicted": 0, "undetermined": 0}
    
    print(f"\nProcessing {len(remaining)} claims with 4-stage pipeline...")
    print("(decompose → support-seek → contradict-seek → synthesize)\n")
    
    for i, evidence_file in enumerate(remaining):
        with open(evidence_file, "r", encoding="utf-8") as f:
            claim_data = json.load(f)
        
        verdict = process_claim(client, claim_data)
        stats[verdict["verdict"]] += 1
        
        output_file = OUTPUT_DIR / f"{claim_data['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=2, ensure_ascii=False)
        
        if (i + 1) % 5 == 0 or i == len(remaining) - 1:
            print(f"  [{i + 1}/{len(remaining)}] {verdict['verdict']} "
                  f"(conf={verdict['confidence']:.2f}, "
                  f"sup={claim_data.get('support_score', 0):.2f}, "
                  f"con={claim_data.get('contradiction_score', 0):.2f})")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    print("\n" + "=" * 60)
    print("REASONING COMPLETE")
    print("=" * 60)
    print(f"  ✅ Supported: {stats['supported']}")
    print(f"  ❌ Contradicted: {stats['contradicted']}")
    print(f"  ⚠️  Undetermined: {stats['undetermined']}")
    
    # Anti-bias check
    total = sum(stats.values())
    if total > 0:
        supported_pct = stats['supported'] / total * 100
        if supported_pct > 80:
            print(f"\n⚠️  WARNING: {supported_pct:.0f}% supported - possible bias")
            print("   Review contradiction thresholds or evidence quality")
    
    logger.info(f"Completed: {stats}")


if __name__ == "__main__":
    main()
