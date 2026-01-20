"""
Dossier Writer Agent - Constraint-linked structured reasoning artifacts.

NovelVerified.AI Pathway-based:
Dossiers are no longer just explanations - they are structured reasoning
artifacts with:
1. Claim → Sub-claims decomposition table
2. Evidence mapping to sub-claims
3. Constraint analysis per sub-claim
4. Verdict justified by constraint violations

This format enables evaluators to trace the reasoning path.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
VERDICTS_DIR = Path("verdicts")
EVIDENCE_DIR = Path("evidence")
OUTPUT_DIR = Path("dossiers")

# Verdict badges
BADGES = {
    "supported": "✅ **SUPPORTED**",
    "contradicted": "❌ **CONTRADICTED**",
    "undetermined": "⚠️ **UNDETERMINED**"
}

# Constraint type descriptions
CONSTRAINT_DESCRIPTIONS = {
    "temporal": "⏱️ Temporal Constraint",
    "capability": "💪 Capability Constraint",
    "commitment": "🤝 Commitment Constraint",
    "world_rule": "🌍 World Rule Constraint",
    "psychological": "🧠 Psychological Constraint",
    "factual": "📋 Factual Constraint"
}


def get_confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar."""
    filled = int(confidence * 10)
    empty = 10 - filled
    return f"[{'█' * filled}{'░' * empty}] {confidence:.0%}"


def format_sub_claims_table(analysis: dict) -> str:
    """
    Format sub-claims as a Markdown table.
    
    This is a key Pathway-based requirement - showing claim decomposition.
    """
    sub_claims = analysis.get("sub_claims", [])
    
    if not sub_claims:
        return "*No sub-claims extracted.*"
    
    rows = ["| ID | Sub-Claim | Type | Verdict |",
            "|:---|:----------|:----:|:-------:|"]
    
    for sc in sub_claims:
        sc_id = sc.get("id", "?")
        text = sc.get("text", "")[:80]
        if len(sc.get("text", "")) > 80:
            text += "..."
        constraint_type = sc.get("type", "factual")
        verdict = sc.get("verdict", "undetermined")
        
        verdict_emoji = "✅" if verdict == "supported" else "❌" if verdict == "contradicted" else "⚠️"
        type_emoji = CONSTRAINT_DESCRIPTIONS.get(constraint_type, constraint_type)[:2]
        
        rows.append(f"| {sc_id} | {text} | {type_emoji} | {verdict_emoji} |")
    
    return "\n".join(rows)


def format_constraint_analysis(analysis: dict) -> str:
    """
    Format constraint violations as structured analysis.
    
    This shows WHY a claim was contradicted based on specific constraints.
    """
    violations = analysis.get("violations", [])
    
    if not violations:
        return "*No constraint violations detected.*"
    
    sections = []
    for v in violations:
        constraint_type = v.get("constraint_type", "unknown")
        description = CONSTRAINT_DESCRIPTIONS.get(constraint_type, constraint_type)
        
        section = f"""#### {description}

**Severity:** {v.get('severity', 'UNKNOWN')}

**Description:** {v.get('description', 'No description')}

**Evidence Position:** {v.get('novel_position', 'UNKNOWN')}

> {v.get('novel_excerpt', 'No excerpt')[:400]}
"""
        sections.append(section)
    
    return "\n---\n".join(sections)


def format_temporal_evidence(evidence: List[dict]) -> str:
    """
    Format evidence organized by temporal slice.
    
    Pathway-based: Shows how evidence from different parts of the novel
    contributes to the verification.
    """
    early = [e for e in evidence if e.get("temporal_slice") == "EARLY"]
    mid = [e for e in evidence if e.get("temporal_slice") == "MID"]
    late = [e for e in evidence if e.get("temporal_slice") == "LATE"]
    
    sections = []
    
    for slice_name, slice_evidence, emoji in [
        ("EARLY (First 30%)", early, "🌅"),
        ("MID (Middle 40%)", mid, "☀️"),
        ("LATE (Final 30%)", late, "🌙")
    ]:
        if not slice_evidence:
            sections.append(f"### {emoji} {slice_name}\n\n*No evidence from this section.*\n")
            continue
        
        section = f"### {emoji} {slice_name}\n\n"
        for i, ev in enumerate(slice_evidence[:2], 1):  # Limit to 2 per slice
            text = ev.get("text", "")[:600]
            if len(ev.get("text", "")) > 600:
                text += "..."
            
            query_type = ev.get("query_type", "standard")
            query_badge = "🔍" if query_type == "standard" else "⚡" if query_type == "counterfactual" else "🔍⚡"
            
            section += f"""**Evidence {i}** {query_badge}
- **Book:** {ev.get('book', 'Unknown')}
- **Chunk:** {ev.get('chunk_idx', '?')}
- **Score:** {ev.get('score', 0):.3f}

> {text}

"""
        sections.append(section)
    
    return "\n".join(sections)


def format_dual_perspective(analysis: dict) -> str:
    """
    Format the dual-perspective analysis (support vs contradiction).
    
    Pathway-based Anti-Bias: Shows that we actively sought both supporting
    AND contradicting evidence.
    """
    support_score = analysis.get("support_score", 0)
    contradict_score = analysis.get("contradiction_score", 0)
    
    support_bar = get_confidence_bar(support_score)
    contradict_bar = get_confidence_bar(contradict_score)
    
    return f"""### 📊 Support Analysis
**Score:** {support_bar}

### 📊 Contradiction Analysis  
**Score:** {contradict_bar}

*Verdict is determined by comparing these scores with calibrated thresholds.*
*Contradiction threshold: 0.4 | Support threshold: 0.7*
"""


def generate_dossier(verdict: dict, evidence_data: dict) -> str:
    """
    Generate a constraint-linked structured dossier.
    
    NovelVerified.AI Pathway-based Requirement:
    - Sub-claims table showing decomposition
    - Constraint analysis per violation
    - Temporal evidence organization
    - Dual-perspective scores (anti-bias)
    """
    claim_id = verdict["claim_id"]
    badge = BADGES.get(verdict.get("verdict", "undetermined"), "❓ **UNKNOWN**")
    confidence_bar = get_confidence_bar(verdict.get("confidence", 0))
    
    # Get extended analysis if available
    analysis = verdict.get("analysis", {})
    
    # Build dossier
    return f"""# Constraint-Linked Dossier: {claim_id}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Pipeline:** NovelVerified.AI Pathway-based - Multi-Stage Constraint-Aware Reasoning

---

## 📋 Claim Information

| Field | Value |
|-------|-------|
| **Claim ID** | {claim_id} |
| **Character** | {evidence_data.get('character', analysis.get('character', 'Unknown'))} |
| **Book** | {evidence_data.get('book_name', analysis.get('book_name', 'Unknown'))} |

### Claim Text

> {evidence_data.get('claim_text', analysis.get('claim_text', 'N/A'))}

---

## 🎯 Verdict

{badge}

**Confidence:** {confidence_bar}

### Reasoning

{verdict.get('reasoning', 'No reasoning provided.')}

---

## 🧩 Claim Decomposition

*The claim was decomposed into atomic sub-claims for individual verification.*

{format_sub_claims_table(analysis)}

---

## ⚖️ Dual-Perspective Evaluation

*Anti-bias mechanism: actively sought BOTH supporting and contradicting evidence.*

{format_dual_perspective(analysis)}

---

## 🚨 Constraint Violations

*Detected conflicts between claim and novel text.*

{format_constraint_analysis(analysis)}

---

## 📚 Temporal Evidence Analysis

*Evidence organized by position in narrative arc.*

{format_temporal_evidence(evidence_data.get('evidence', []))}

---

## 📝 Key Spans

### Supporting Evidence
{format_spans(verdict.get('supporting_spans', []), 'supporting', '📗')}

### Contradicting Evidence
{format_spans(verdict.get('contradicting_spans', []), 'contradicting', '📕')}

---

*This dossier was automatically generated by NovelVerified.AI*
*NovelVerified.AI Pathway-based: Pathway-based Multi-Stage Constraint-Aware Reasoning*
"""


def format_spans(spans: List, label: str, emoji: str) -> str:
    """Format supporting/contradicting spans."""
    if not spans:
        return f"*No {label.lower()} spans identified.*"
    
    items = []
    for span in spans[:5]:
        if isinstance(span, dict):
            text = span.get("text", str(span))[:200]
        else:
            text = str(span)[:200]
        items.append(f'{emoji} "{text}"')
    
    return "\n".join(items)


def main():
    """Main entry point for dossier writer agent."""
    print("=" * 60)
    print("DOSSIER WRITER AGENT - Constraint-Linked Artifacts")
    print("NovelVerified.AI Pathway-based: Structured reasoning documentation")
    print("=" * 60)
    
    verdict_files = list(VERDICTS_DIR.glob("*.json"))
    if not verdict_files:
        print(f"ERROR: No verdict files found in {VERDICTS_DIR}/")
        return
    
    print(f"Found {len(verdict_files)} verdict files")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for i, verdict_file in enumerate(verdict_files):
        claim_id = verdict_file.stem
        
        with open(verdict_file, "r", encoding="utf-8") as f:
            verdict = json.load(f)
        
        evidence_file = EVIDENCE_DIR / f"{claim_id}.json"
        if evidence_file.exists():
            with open(evidence_file, "r", encoding="utf-8") as f:
                evidence_data = json.load(f)
        else:
            evidence_data = {"evidence": []}
        
        dossier = generate_dossier(verdict, evidence_data)
        
        output_file = OUTPUT_DIR / f"{claim_id}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(dossier)
        
        if (i + 1) % 20 == 0 or i == len(verdict_files) - 1:
            print(f"  Generated {i + 1}/{len(verdict_files)} dossiers")
    
    print("=" * 60)
    print(f"Dossiers saved to {OUTPUT_DIR}/")
    print("  - Sub-claims decomposition table")
    print("  - Constraint violation analysis")
    print("  - Temporal evidence organization")
    print("  - Dual-perspective scores")


if __name__ == "__main__":
    main()
