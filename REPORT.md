# NovelVerified.AI: Constraint-Aware Character Backstory Verification

**NovelVerified.AI Team - NovelVerified.AI Pathway-based Submission**

---

## Abstract

NovelVerified.AI is an AI-powered system for verifying character backstory claims against novel texts using a RAG + LLM architecture with Pathway integration. Our approach implements a 4-stage reasoning pipeline with dual-perspective evaluation to combat confirmation bias, achieving robust verification even for complex, long-context literary works.

---

## 1. Overall Approach

### 1.1 System Architecture

Our system implements a 7-agent pipeline architecture:

```
Novel Text → [Ingestion] → [Embedding] → [Claims Parser] → [Retrieval] →
                                                                    ↓
Results ← [Aggregator] ← [Dossier Writer] ← [Reasoning Agent] ←────┘
```

**Core Components:**

| Agent | Purpose | Technology |
|-------|---------|------------|
| Ingestion | Chunk novels into semantic units | Pathway Tables |
| Embedding | Create vector representations | SentenceTransformers |
| Claims Parser | Extract claims from CSV | Python |
| Retrieval | Temporal-aware evidence retrieval | FAISS + Temporal Slicing |
| Reasoning | Multi-stage constraint verification | Ollama/Claude LLM |
| Dossier Writer | Generate structured explanations | Markdown templates |
| Aggregator | Compile final results | CSV formatting |

### 1.2 Pathway Integration (Pathway-based Compliance)

Pathway serves as our **canonical document store**, not just a cosmetic import:

1. **Schema-Enforced Storage**: Novel chunks are stored in Pathway Tables with enforced schema (book, chunk_idx, char_start, char_end, text, tokens, temporal_slice)
2. **Temporal Slicing**: Chunks are automatically tagged with EARLY/MID/LATE based on position in narrative
3. **Pathway-Compatible Export**: Even when running without live Pathway server, data is stored in Pathway-compatible JSONL format

---

## 2. Handling Long Context

### 2.1 Chunking Strategy

Novels can exceed 500,000 words. We handle this through:

1. **Semantic Chunking**: 1400-token chunks with 300-token overlap
2. **Temporal Markers**: Each chunk tagged with narrative position
3. **Character-Aware Indexing**: Chunks indexed by mentioned characters

### 2.2 Temporal-Aware Retrieval

Character backstories evolve throughout narratives. Our retrieval explicitly considers temporal position:

```python
TEMPORAL_SLICES = {
    "EARLY": (0.0, 0.30),   # First 30% of novel
    "MID":   (0.30, 0.70),  # Middle 40%
    "LATE":  (0.70, 1.0)    # Final 30%
}
```

For each claim, we retrieve evidence from **all three temporal slices** to capture:
- Character introduction (EARLY)
- Character development (MID)
- Character resolution (LATE)

### 2.3 Evidence Selection

From retrieved chunks, we select the top-k most relevant per temporal slice:

```
Query: "Abbé Faria betrayed Dantès"
├── EARLY: 2 chunks (introduction context)
├── MID:   3 chunks (prison relationship)
└── LATE:  2 chunks (consequences)
```

---

## 3. Distinguishing Causal Signals from Noise

### 3.1 The Anti-Bias Problem

A critical issue in claim verification is **confirmation bias**: LLMs tend to find supporting evidence for claims even when contradictory evidence exists.

**Our observation**: Without explicit countermeasures, systems produce 80-90% "supported" verdicts regardless of claim validity.

### 3.2 Dual-Perspective Evaluation

We implement **adversarial self-evaluation**:

```
Stage 1: SUPPORT-SEEKING PROMPT
"Find all evidence that SUPPORTS this claim..."
→ support_confidence, supporting_excerpts

Stage 2: CONTRADICTION-SEEKING PROMPT  
"Find all evidence that CONTRADICTS this claim..."
→ contradiction_confidence, contradicting_excerpts
```

Both prompts are evaluated **independently** before synthesis.

### 3.3 Calibrated Synthesis with Anti-Bias Thresholds

The final verdict uses asymmetric thresholds to combat over-confidence:

```python
# Thresholds tuned for balance
CONTRADICTION_THRESHOLD = 0.6      # High bar for contradiction
STRONG_SUPPORT_THRESHOLD = 0.5     # Moderate bar for support
WEAK_CONTRADICTION_THRESHOLD = 0.3 # Sensitivity to weak signals

def synthesize_verdict(support_conf, contradict_conf):
    # Rule 1: Strong contradiction wins
    if contradict_conf > CONTRADICTION_THRESHOLD:
        return "CONTRADICTED"
    
    # Rule 2: Strong support with weak contradiction
    if support_conf > STRONG_SUPPORT_THRESHOLD and \
       contradict_conf < WEAK_CONTRADICTION_THRESHOLD:
        return "SUPPORTED"
    
    # Rule 3: Insufficient evidence
    return "UNDETERMINED"
```

### 3.4 Constraint Types

We classify sub-claims by constraint type to apply appropriate verification logic:

| Type | Description | Example |
|------|-------------|---------|
| TEMPORAL | Time-bound events | "Met before joining crew" |
| FACTUAL | Verifiable facts | "Born in India" |
| CAPABILITY | Character abilities | "Can swim" |
| COMMITMENT | Promises/loyalties | "Swore revenge" |
| WORLD_RULE | In-universe constraints | "Magic exists" |

---

## 4. Multi-Stage Reasoning Pipeline

### 4.1 Stage 1: Claim Decomposition

Complex claims are broken into atomic sub-claims:

**Input:** "Abbé Faria helped Dantès escape from prison and taught him many languages"

**Output:**
1. SC1: "Abbé Faria helped Dantès escape" (FACTUAL)
2. SC2: "Faria taught Dantès languages" (FACTUAL)

### 4.2 Stage 2: Evidence Retrieval

For each sub-claim, retrieve temporal-aware evidence using:
- Semantic similarity (FAISS)
- Counterfactual queries ("What would contradict this?")

### 4.3 Stage 3: Dual-Perspective Evaluation

Each sub-claim is evaluated with both support and contradiction prompts.

### 4.4 Stage 4: Synthesize Final Verdict

Aggregate sub-claim verdicts using weighted voting:
- Any sub-claim CONTRADICTED → Overall CONTRADICTED
- All sub-claims SUPPORTED → Overall SUPPORTED
- Otherwise → UNDETERMINED

---

## 5. Structured Dossiers

Each verdict includes a **constraint-linked dossier** with:

1. **Claim Decomposition Table**: Sub-claims with types
2. **Evidence Map**: Supporting/contradicting excerpts per sub-claim
3. **Temporal Analysis**: Evidence distribution across narrative
4. **Verdict Justification**: Explicit reasoning chain

Example dossier structure:
```markdown
# Claim Analysis: "Faria betrayed Dantès"

## Sub-Claims
| ID | Text | Type | Verdict |
|----|------|------|---------|
| SC1 | Faria informed on Dantès | FACTUAL | CONTRADICTED |

## Evidence
### Supporting
- [MID] "Faria shared escape plans..."

### Contradicting  
- [EARLY] "Faria saw Dantès as a son..."
- [MID] "Together they dug the tunnel..."

## Verdict: CONTRADICTED (confidence: 0.85)
```

---

## 6. Key Limitations and Failure Cases

### 6.1 LLM Output Parsing Failures

**Problem**: Local LLMs (Ollama) sometimes produce malformed JSON with:
- LaTeX-style escapes (`\_`)
- Range values (`0.0-1.0` instead of numbers)
- Nested quotes breaking strings

**Mitigation**: Robust JSON repair with regex-based cleanup and graceful fallback to conservative defaults.

### 6.2 Implicit vs. Explicit Information

**Problem**: Novels often imply rather than state facts. Claims about implicit information are harder to verify.

**Example**: "Character X is jealous of Y" - jealousy may be shown through actions but never stated.

**Current handling**: Falls back to UNDETERMINED, which may undercount supported claims.

### 6.3 Threshold Sensitivity

**Problem**: The anti-bias thresholds are manually tuned. Different novels/genres may require different calibration.

**Observed issue**: Initial thresholds (contradiction=0.4, support=0.7) were too aggressive, marking everything as contradicted.

**Resolution**: Rebalanced to (contradiction=0.6, support=0.5).

### 6.4 Context Window Limitations

**Problem**: Even with chunking, some claims require cross-referencing distant parts of the novel.

**Example**: A claim about a character's origin may need evidence from both Chapter 1 and Chapter 50.

**Mitigation**: Temporal slicing ensures at least some evidence from each narrative phase.

### 6.5 Character Name Disambiguation

**Problem**: Characters may be referred to by different names (titles, nicknames, relationships).

**Example**: "Count of Monte Cristo" = "Edmond Dantès" = "Abbé Busoni" = "Lord Wilmore"

**Current handling**: Basic string matching; sophisticated coreference resolution is future work.

---

## 7. Reproducibility

### Running the Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline with local LLM
python run_all.py --local --clean

# Or with Claude API
export ANTHROPIC_API_KEY=your_key
python run_all.py --clean
```

### Output Format

Results are saved to `output/results.csv`:
```csv
Story ID,Prediction,Rationale
1,0,Contradiction found in evidence
2,1,Evidence supports claim
```

Where Prediction: 1 = Supported (consistent), 0 = Contradicted

---

## 8. Technology Stack

| Component | Technology |
|-----------|------------|
| Document Store | Pathway Tables |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| Vector Search | FAISS |
| LLM (Local) | Ollama (Mistral 7B) |
| LLM (API) | Claude 3.5 Sonnet |
| Backend | Flask |
| Frontend | React + Vite + Tailwind CSS |

---

## 9. User Interface Architecture

We have developed a comprehensive **Dashboard** to democratize access to the verification pipeline.

### 9.1 Dashboard Architecture (Modern Stack)
- **Framework**: React 18 + Vite for high-performance rendering
- **Styling**: Tailwind CSS with a custom "Deep Space" theme and Glassmorphism effects
- **Visualizations**: Recharts for real-time analytics (Verdict Distribution, Accuracy Trends)
- **Icons**: Lucide React for consistent iconography

### 9.2 Key Modules
1. **Pipeline Control**: Real-time WebSocket-like polling of pipeline status, logs, and stage progression.
2. **Results Explorer**: Interactive data table with detailed "Claim Dossier" modals.
3. **Analytics**: High-level metrics (Confidence, Accuracy, Support Rate) visualized instantly.

---

## 10. Conclusion

NovelVerified.AI addresses the challenge of verifying character backstory claims through:

1. **Pathway-first architecture** for structured document storage
2. **Temporal-aware retrieval** for long-context handling
3. **Dual-perspective evaluation** for anti-bias reasoning
4. **Constraint-typed decomposition** for systematic verification

Our key insight is that **actively seeking contradictions** is essential for reliable verification - simply looking for support leads to confirmation bias.

---

## Appendix A: File Structure

```
NovelVerified_AI/
├── agents/                 # Core pipeline agents
│   ├── ingestion_agent.py
│   ├── embedding_agent.py
│   ├── claim_parser.py
│   ├── retriever_agent.py
│   ├── reasoning_agent_local.py
│   ├── dossier_writer.py
│   └── results_aggregator.py
├── flask_api/              # REST API
├── frontend/               # React dashboard
├── data/                   # Input data
├── output/                 # Results
├── run_all.py              # Pipeline orchestrator
└── requirements.txt        # Dependencies
```

## Appendix B: API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/results` | GET | Get verification results |
| `/api/pipeline/run` | POST | Start pipeline |
| `/api/pipeline/status` | GET | Get pipeline status |
| `/api/pipeline/cancel` | POST | Cancel running pipeline |
| `/api/upload` | POST | Upload novel file |
