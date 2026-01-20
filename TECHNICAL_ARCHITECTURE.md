# Pathway-based Technical Justification

## NovelVerified.AI - NovelVerified.AI Team

This document provides the technical justification for Pathway-based compliance,
suitable for inclusion in the 10-page submission report.

---

## 1. Pathway Framework Integration

### Why Pathway is Structurally Necessary

Our system uses **Pathway as the canonical document store**, not merely as an import.
The pipeline cannot function without Pathway because:

1. **Document Ingestion** (`agents/ingestion_agent.py`)
   - Chunks are created and stored via `PathwayDocumentStore`
   - Temporal slicing (EARLY/MID/LATE) is computed during ingestion
   - The JSONL export for FAISS is a *derived output*, not the source of truth

2. **Chunk Storage Schema** (`agents/pathway_store.py`)
   - Uses Pathway Table schema with typed columns
   - Stores: `chunk_id`, `book`, `temporal_slice`, `text`, `char_start/end`
   - Enables streaming-compatible iteration

3. **Retrieval Mediation**
   - Retrieval queries are enriched with temporal metadata from Pathway store
   - Temporal slicing enables constraint-aware reasoning across narrative arc

### Alternative Approaches Considered

| Approach | Problem | Why We Chose Pathway |
|----------|---------|---------------------|
| Direct file I/O | No streaming, no schema | Pathway provides typed tables |
| SQLite | Not streaming-compatible | Pathway fits RAG pipeline better |
| Pure FAISS | No metadata management | Pathway handles chunk metadata |

---

## 2. Long-Context Handling

### Chunking Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 1400 tokens | Fits in LLM context with room for prompt |
| Overlap | 300 tokens | Preserves context across boundaries |
| Encoding | cl100k_base | Compatible with GPT-4/Claude tokenizers |

### Temporal Slicing

We divide each novel into three temporal zones:

- **EARLY (0-30%)**: Character introductions, world-building
- **MID (30-70%)**: Main plot events, character development  
- **LATE (70-100%)**: Resolutions, final revelations

This enables:
- Detecting temporal constraint violations (e.g., "knew before meeting")
- Tracking character arc consistency
- Prioritizing late-novel evidence for backstory claims

### Retrieval Strategy

```
1. Standard query: "Character: Claim text"
2. Counterfactual query: "Character: negated claim"
3. Retrieve top-K from EACH temporal slice
4. Combine with temporal diversity
```

---

## 3. Separating Causal Signals from Noise

### Multi-Stage Reasoning Pipeline

Our system avoids the naive `retrieve → ask LLM → verdict` pattern.
Instead, we use a 4-stage pipeline:

```
┌─────────────┐    ┌──────────────┐    ┌────────────┐    ┌────────────┐
│  DECOMPOSE  │ → │   RETRIEVE   │ → │  EVALUATE  │ → │ SYNTHESIZE │
│  sub-claims │    │  temporal    │    │  dual-     │    │  calibrate │
│             │    │  evidence    │    │  perspective│    │  verdict   │
└─────────────┘    └──────────────┘    └────────────┘    └────────────┘
```

### Constraint Categories

| Type | Description | Example Detection |
|------|-------------|-------------------|
| TEMPORAL | Event ordering | "Knew X before meeting Y" |
| CAPABILITY | What character can do | "Could not swim" vs swimming scene |
| COMMITMENT | Promises, oaths | Betrayal vs claimed loyalty |
| WORLD_RULE | Physical/magical laws | Impossible actions in universe |
| PSYCHOLOGICAL | Beliefs, fears | Actions contradicting stated fears |

### Dual-Perspective Evaluation (Anti-Bias)

To prevent "supported" bias, we actively seek contradictions:

```python
# Support-seeking prompt
"Find evidence that SUPPORTS this claim being TRUE..."

# Contradiction-seeking prompt  
"Find evidence that CONTRADICTS this claim or makes it IMPOSSIBLE..."
```

### Confidence Calibration

```python
CONTRADICTION_THRESHOLD = 0.4   # Any > 0.4 → contradicted
STRONG_SUPPORT_THRESHOLD = 0.7  # Need > 0.7 AND low contradiction
WEAK_CONTRADICTION = 0.25       # Below this, support can override
```

---

## 4. Novelty Beyond Basic RAG

| Feature | Basic RAG | Our System |
|---------|-----------|------------|
| Retrieval | Semantic similarity | Temporal + counterfactual |
| Reasoning | Single prompt | 4-stage decomposition |
| Bias handling | None | Dual-perspective + thresholds |
| Evidence linking | Similarity score | Constraint type classification |
| Output | Verdict only | Structured dossier with sub-claims |

---

## 5. Reproducibility

### Running the Pipeline

```bash
# Full pipeline with Claude API
python run_all.py --clean

# Full pipeline with local LLM
python run_all.py --clean --local
```

### Dependencies

- `pathway>=0.28.0` (Pathway-based requirement)
- `anthropic>=0.30.0` (Claude API)
- `sentence-transformers` (embeddings)
- `faiss-cpu` (vector search)

### Output Format

```csv
Story ID,Prediction,Rationale
95,1,Evidence supports claim about Villefort's early career.
136,0,Temporal constraint violated: character knew information before meeting.
```

---

## 6. Limitations and Future Work

### Current Limitations

1. **Context window**: Cannot process entire novel in one call
2. **Local LLM quality**: Ollama models less reliable than Claude
3. **Ground truth**: Limited labeled training data

### Potential Improvements

1. Hierarchical summarization for global context
2. Fine-tuned contradiction classifier
3. Entity coreference resolution for character tracking

---

*NovelVerified.AI Team - NovelVerified.AI*
