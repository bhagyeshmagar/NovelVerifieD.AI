"""
Local Reasoning Agent - Multi-stage constraint-aware verification with Ollama.

KDSH 2026 Track A:
Same 4-stage pipeline as the Claude version but using local Ollama LLM:
1. DECOMPOSE: Break claim into atomic sub-claims
2. RETRIEVE: (done by retriever_agent)
3. EVALUATE: Dual-perspective (support + contradict)
4. SYNTHESIZE: Calibrated verdict

Anti-bias features preserved:
- Dual prompts for support AND contradiction
- Confidence calibration thresholds
- Constraint violation detection
"""

import json
import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Import constraint types
from constraint_types import (
    ConstraintType, Verdict, SubClaim, ConstraintViolation, ClaimAnalysis,
    DECOMPOSITION_PROMPT, SUPPORT_SEEKING_PROMPT,
    CONTRADICTION_SEEKING_PROMPT
)

load_dotenv()

# ============================================================================
# Logging
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('reasoning_agent_local.log', mode='a')
    ]
)
logger = logging.getLogger('reasoning_agent_local')

# ============================================================================
# Configuration
# ============================================================================
EVIDENCE_DIR = Path("evidence")
OUTPUT_DIR = Path("verdicts")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct-q4_0")

RATE_LIMIT_DELAY = 0.2

# Anti-bias thresholds
CONTRADICTION_THRESHOLD = 0.4
STRONG_SUPPORT_THRESHOLD = 0.7
WEAK_CONTRADICTION_THRESHOLD = 0.25


# ============================================================================
# Ollama LLM Call
# ============================================================================

def call_ollama(prompt: str, claim_id: str, stage: str) -> Optional[dict]:
    """Call Ollama API and parse JSON response."""
    system = "You output valid JSON only. No markdown, no commentary."
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024,
                    "top_p": 0.9
                }
            },
            timeout=180
        )
        
        if response.status_code != 200:
            logger.error(f"{claim_id}/{stage}: Ollama error {response.status_code}")
            return None
        
        text = response.json().get("response", "").strip()
        
        # Handle markdown blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        return json.loads(text)
        
    except json.JSONDecodeError as e:
        logger.warning(f"{claim_id}/{stage}: JSON parse error - {e}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"{claim_id}/{stage}: Cannot connect to Ollama")
        return None
    except Exception as e:
        logger.error(f"{claim_id}/{stage}: Error - {e}")
        return None


# ============================================================================
# Multi-Stage Pipeline
# ============================================================================

def decompose_claim(claim_data: dict) -> List[SubClaim]:
    """Decompose claim into sub-claims."""
    prompt = DECOMPOSITION_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data.get("character", "Unknown"),
        book_name=claim_data.get("book_name", "Unknown")
    )
    
    result = call_ollama(prompt, claim_data["claim_id"], "decompose")
    
    if not result or not isinstance(result, list):
        return [SubClaim(
            id="SC1",
            text=claim_data["claim_text"],
            constraint_type=ConstraintType.FACTUAL,
            parent_claim_id=claim_data["claim_id"]
        )]
    
    sub_claims = []
    for item in result:
        try:
            ctype = ConstraintType(item.get("type", "factual").lower())
        except ValueError:
            ctype = ConstraintType.FACTUAL
        
        sub_claims.append(SubClaim(
            id=item.get("id", f"SC{len(sub_claims)+1}"),
            text=item.get("text", ""),
            constraint_type=ctype,
            parent_claim_id=claim_data["claim_id"]
        ))
    
    return sub_claims if sub_claims else [SubClaim(
        id="SC1",
        text=claim_data["claim_text"],
        constraint_type=ConstraintType.FACTUAL,
        parent_claim_id=claim_data["claim_id"]
    )]


def evaluate_support(claim_data: dict, evidence_text: str) -> Tuple[float, str, List[str]]:
    """Seek supporting evidence."""
    prompt = SUPPORT_SEEKING_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data.get("character", "Unknown"),
        evidence_text=evidence_text
    )
    
    result = call_ollama(prompt, claim_data["claim_id"], "support")
    
    if not result:
        return 0.0, "Failed to analyze", []
    
    return (
        float(result.get("support_confidence", 0.0)),
        result.get("support_reasoning", "No reasoning"),
        result.get("supporting_excerpts", [])
    )


def evaluate_contradiction(claim_data: dict, evidence_text: str) -> Tuple[float, str, List[str], str]:
    """Seek contradicting evidence (ANTI-BIAS)."""
    prompt = CONTRADICTION_SEEKING_PROMPT.format(
        claim_text=claim_data["claim_text"],
        character=claim_data.get("character", "Unknown"),
        evidence_text=evidence_text
    )
    
    result = call_ollama(prompt, claim_data["claim_id"], "contradict")
    
    if not result:
        return 0.0, "Failed to analyze", [], "none"
    
    return (
        float(result.get("contradiction_confidence", 0.0)),
        result.get("contradiction_reasoning", "No reasoning"),
        result.get("contradicting_excerpts", []),
        result.get("violation_type", "none")
    )


def synthesize_verdict(support_conf: float, support_reason: str,
                       contradict_conf: float, contradict_reason: str,
                       violation_type: str) -> Tuple[Verdict, float, str]:
    """Synthesize final verdict with anti-bias calibration."""
    
    # Rule 1: Strong contradiction wins
    if contradict_conf > CONTRADICTION_THRESHOLD:
        confidence = min(0.95, contradict_conf + 0.1)
        reasoning = f"Contradiction ({violation_type}): {contradict_reason}"
        return Verdict.CONTRADICTED, confidence, reasoning
    
    # Rule 2: Strong support with weak contradiction
    if support_conf > STRONG_SUPPORT_THRESHOLD and contradict_conf < WEAK_CONTRADICTION_THRESHOLD:
        confidence = support_conf * 0.9
        reasoning = f"Evidence supports: {support_reason}"
        return Verdict.SUPPORTED, confidence, reasoning
    
    # Rule 3: Ambiguous
    confidence = max(0.3, min(support_conf, 0.5))
    reasoning = "Insufficient evidence for definitive verdict"
    return Verdict.UNDETERMINED, confidence, reasoning


def process_claim(claim_data: dict) -> dict:
    """Process claim through 4-stage pipeline."""
    claim_id = claim_data["claim_id"]
    
    # Stage 1: Decomposition
    sub_claims = decompose_claim(claim_data)
    
    # Prepare evidence
    evidence = claim_data.get("evidence", [])
    evidence_text = "\n\n".join([
        f"[{e.get('temporal_slice', 'MID')}] {e['text'][:1200]}"
        for e in evidence[:4]
    ])
    
    # Stage 2: Dual-perspective evaluation
    support_conf, support_reason, support_excerpts = evaluate_support(
        claim_data, evidence_text
    )
    
    time.sleep(0.3)
    
    contradict_conf, contradict_reason, contradict_excerpts, violation_type = evaluate_contradiction(
        claim_data, evidence_text
    )
    
    # Stage 3: Synthesis
    verdict, confidence, reasoning = synthesize_verdict(
        support_conf, support_reason,
        contradict_conf, contradict_reason,
        violation_type
    )
    
    # Build analysis
    analysis = ClaimAnalysis(
        claim_id=claim_id,
        claim_text=claim_data["claim_text"],
        character=claim_data.get("character", "Unknown"),
        book_name=claim_data.get("book_name", "Unknown"),
        sub_claims=sub_claims,
        support_score=support_conf,
        contradiction_score=contradict_conf,
        verdict=verdict,
        confidence=confidence,
        reasoning=reasoning
    )
    
    return {
        "claim_id": claim_id,
        "verdict": verdict.value,
        "confidence": round(confidence, 2),
        "supporting_spans": support_excerpts[:3],
        "contradicting_spans": contradict_excerpts[:3],
        "reasoning": reasoning[:300],
        "analysis": analysis.to_dict()
    }


# ============================================================================
# Ollama Status Check
# ============================================================================

def check_ollama_status() -> bool:
    """Check if Ollama is running with required model."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        if not any(OLLAMA_MODEL in name for name in model_names):
            print(f"\n⚠️  Model '{OLLAMA_MODEL}' not found!")
            print(f"   Available: {model_names}")
            print(f"   Install: ollama pull {OLLAMA_MODEL}")
            return False
        
        return True
    except:
        return False


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point for local multi-stage reasoning agent."""
    print("=" * 60)
    print("LOCAL REASONING AGENT - Multi-Stage Pipeline")
    print("KDSH 2026 Track A: Ollama with anti-bias reasoning")
    print("=" * 60)
    
    logger.info("Starting local reasoning agent")
    
    print(f"\nChecking Ollama at {OLLAMA_HOST}...")
    if not check_ollama_status():
        print("\n❌ Ollama not available!")
        print("   1. Install: curl -fsSL https://ollama.com/install.sh | sh")
        print(f"   2. Pull model: ollama pull {OLLAMA_MODEL}")
        print("   3. Start: ollama serve")
        return
    
    print(f"✅ Ollama running with model: {OLLAMA_MODEL}")
    
    evidence_files = list(EVIDENCE_DIR.glob("*.json"))
    if not evidence_files:
        print(f"\n❌ No evidence files in {EVIDENCE_DIR}/")
        return
    
    print(f"Found {len(evidence_files)} evidence files")
    print(f"\nAnti-bias thresholds:")
    print(f"  - Contradiction: {CONTRADICTION_THRESHOLD}")
    print(f"  - Strong support: {STRONG_SUPPORT_THRESHOLD}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    processed = set(f.stem for f in OUTPUT_DIR.glob("*.json"))
    remaining = [f for f in evidence_files if f.stem not in processed]
    
    if processed:
        print(f"  {len(processed)} processed, {len(remaining)} remaining")
    
    print(f"\nProcessing {len(remaining)} claims with 4-stage pipeline...")
    
    stats = {"supported": 0, "contradicted": 0, "undetermined": 0}
    start_time = time.time()
    
    for i, evidence_file in enumerate(remaining):
        with open(evidence_file, "r", encoding="utf-8") as f:
            claim_data = json.load(f)
        
        verdict = process_claim(claim_data)
        stats[verdict["verdict"]] += 1
        
        output_file = OUTPUT_DIR / f"{claim_data['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        avg = elapsed / (i + 1)
        eta = avg * (len(remaining) - i - 1)
        
        if (i + 1) % 5 == 0 or i == len(remaining) - 1:
            print(f"  [{i + 1}/{len(remaining)}] {verdict['verdict']} "
                  f"(conf={verdict['confidence']:.2f}) - ETA: {eta/60:.1f}min")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"Completed in {total_time/60:.1f} minutes")
    print("=" * 60)
    print(f"  ✅ Supported: {stats['supported']}")
    print(f"  ❌ Contradicted: {stats['contradicted']}")
    print(f"  ⚠️  Undetermined: {stats['undetermined']}")
    
    # Anti-bias warning
    total = sum(stats.values())
    if total > 0:
        supported_pct = stats['supported'] / total * 100
        if supported_pct > 80:
            print(f"\n⚠️  WARNING: {supported_pct:.0f}% supported - review thresholds")
    
    logger.info(f"Completed: {stats}")


if __name__ == "__main__":
    main()
