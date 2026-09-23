# Evidence-Grounded LLM Log Triage for Incident Response

<p align="center">

<img src="https://img.shields.io/github/license/priyanshu015211/LLM-Powered-Log-Triage?style=for-the-badge" alt="License">
<img src="https://img.shields.io/github/stars/priyanshu015211/LLM-Powered-Log-Triage?style=for-the-badge" alt="Stars">
<img src="https://img.shields.io/github/forks/priyanshu015211/LLM-Powered-Log-Triage?style=for-the-badge" alt="Forks">
<img src="https://img.shields.io/github/issues/priyanshu015211/LLM-Powered-Log-Triage?style=for-the-badge" alt="Issues">
<img src="https://img.shields.io/github/issues-pr/priyanshu015211/LLM-Powered-Log-Triage?style=for-the-badge" alt="Pull Requests">
<img src="https://img.shields.io/github/actions/workflow/status/priyanshu015211/LLM-Powered-Log-Triage/pr-checks.yml?branch=main&style=for-the-badge" alt="CI">

</p>

<p align="center">

<img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/LLM-Enabled-8A2BE2?style=for-the-badge" alt="LLM">
<img src="https://img.shields.io/badge/Research-Oriented-FF6F00?style=for-the-badge" alt="Research">
<img src="https://img.shields.io/badge/RCA-Root%20Cause%20Analysis-DC143C?style=for-the-badge" alt="RCA">
<img src="https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge" alt="Status">

</p>

> **Evidence-Grounded Root-Cause Analysis for Distributed-System Incidents**

A research-oriented framework that combines semantic log analysis, temporal relationships, service dependencies, evidence verification, and Large Language Models (LLMs) to investigate the reliability and efficiency of automated root-cause analysis.

## Overview

Modern distributed applications generate large volumes of heterogeneous logs. A single underlying failure can propagate through dependent services and produce multiple secondary errors.

This project investigates whether structured semantic, temporal, service-dependency, supporting, and contradictory evidence can improve LLM-based root-cause analysis compared with less-structured approaches.

The system treats an LLM-generated root cause as a **hypothesis** unless sufficient evidence supports it. It is designed as decision support for engineers rather than autonomous incident response.

## Research Question

> **Does evidence-grounded reasoning improve LLM-based root-cause analysis compared with less-structured LLM approaches?**

### Research Questions

- **RQ1:** How accurately can an evidence-grounded LLM framework identify incident root causes?
- **RQ2:** Does combining semantic, temporal, and service-dependency evidence improve RCA ranking?
- **RQ3:** Does evidence verification reduce unsupported explanations?
- **RQ4:** What trade-off exists between RCA accuracy, latency, token usage, LLM calls, and cost?
- **RQ5:** How robust is the system to noise, duplicates, missing evidence, contradictions, and long contexts?

## Research Contributions

- Semantic event grouping
- Temporal event graph
- Service dependency graph
- Explicit evidence builder
- LLM-based RCA hypothesis generation
- Supporting and contradictory evidence
- Evidence verification
- Quantitative RCA ranking
- Incident timeline reconstruction
- Baseline comparisons
- Ablation studies
- Robustness experiments
- RCA-specific evaluation metrics
- LLM cost and latency analysis
- Reproducible experiment pipeline

## System Architecture

```text
                         RAW LOGS
                            |
                            v
                  LOG INGESTION & PARSING
                            |
                            v
                     EVENT EXTRACTION
                            |
                            v
                  SEMANTIC EVENT GROUPING
                            |
                 +----------+----------+
                 |                     |
                 v                     v
          TEMPORAL EVENT        SERVICE DEPENDENCY
              GRAPH                    GRAPH
                 |                     |
                 +----------+----------+
                            |
                            v
                     EVIDENCE BUILDER
                            |
                            v
                LLM HYPOTHESIS GENERATION
                            |
                            v
                    EVIDENCE VERIFICATION
                       /            \
                      /              \
             SUPPORTING          CONTRADICTING
              EVIDENCE             EVIDENCE
                    \                /
                     \              /
                      v            v
                       RCA RANKING
                       |          |
                       v          v
                  ROOT CAUSE   TIMELINE
                       \          /
                        \        /
                         v      v
                     INCIDENT DASHBOARD
```

## Core Components

### 1. Log Ingestion and Parsing

Convert supported log formats into a common internal representation.

Target fields:

```text
timestamp
log_level
service
host
message
exception
request_id
trace_id
source
metadata
```

### 2. Preprocessing and Event Extraction

Normalize logs, validate timestamps, extract severity/service/message fields, and convert entries into traceable structured events.

Example:

```json
{
  "event_id": "E17",
  "timestamp": "2026-09-23T14:02:18",
  "service": "database",
  "severity": "ERROR",
  "template": "database connection timeout",
  "message": "Connection to db-primary timed out",
  "request_id": "REQ-42"
}
```

### 3. Semantic Event Grouping

Example:

```text
Database connection refused
Database connection timeout
Unable to establish database connection
DB connection failed
                |
                v
      DATABASE CONNECTIVITY FAILURE
```

Candidate methods:

- Sentence Transformers
- Cosine similarity
- DBSCAN
- HDBSCAN
- Threshold-based clustering

### 4. Temporal Event Graph

Represent event ordering and time differences to distinguish potential initiating events from downstream symptoms.

```text
E01: DB latency increased
          |
          v
E02: DB timeout
          |
          v
E03: API timeout
          |
          v
E04: Payment service failure
```

### 5. Service Dependency Graph

Represent relationships such as:

```text
User Service
     |
     v
Payment API
     |
     v
Database
```

### 6. Evidence Builder

Build structured evidence before LLM reasoning.

```json
{
  "candidate_event": "E02",
  "supporting_events": ["E01", "E03", "E04"],
  "temporal_score": 0.91,
  "semantic_score": 0.88,
  "dependency_score": 0.94,
  "severity_score": 0.80,
  "contradicting_events": ["E19"]
}
```

The values above are illustrative; actual values must come from implementation and experiments.

### 7. LLM Hypothesis Generation

The LLM receives structured evidence and returns multiple hypotheses when appropriate.

```json
{
  "hypotheses": [
    {
      "root_cause": "Database connectivity failure",
      "supporting_events": ["E01", "E02"],
      "contradicting_events": [],
      "explanation": "...",
      "status": "potential"
    }
  ]
}
```

### 8. Evidence Verification

```text
LLM Hypothesis
      |
      v
Retrieve cited evidence
      |
      v
Evidence exists?
      |
      v
Temporal consistency?
      |
      v
Service consistency?
      |
      v
Contradictory evidence?
      |
      v
Verification result
```

Possible statuses:

```text
SUPPORTED
PARTIALLY_SUPPORTED
INSUFFICIENT_EVIDENCE
CONTRADICTED
```

### 9. RCA Ranking

Proposed scoring framework:

```text
R(C) =
    wt * TemporalEvidence
  + ws * SeverityEvidence
  + wf * FrequencyEvidence
  + wd * DependencyEvidence
  + wm * SemanticEvidence
  + we * SupportingEvidence
  - wc * ContradictionEvidence
```

Weights will be determined experimentally or through a documented heuristic configuration.

### 10. Incident Timeline

```text
14:02:10  Database latency increase
14:02:18  Database connection timeout
14:02:21  API timeout
14:02:25  Payment service failure
14:02:31  User request failure
```

## Experimental Design

### Baseline A — Direct LLM

```text
Raw / minimally filtered logs
          |
          v
         LLM
          |
          v
         RCA
```

### Baseline B — Semantic LLM

```text
Logs
 |
 v
Semantic Grouping
 |
 v
LLM
 |
 v
RCA
```

### Baseline C — Evidence-Grounded Without Verification

```text
Logs
 |
 v
Semantic + Temporal + Dependency Evidence
 |
 v
LLM
 |
 v
RCA
```

### Proposed System

```text
Logs
 |
 v
Semantic + Temporal + Dependency Evidence
 |
 v
LLM Hypothesis Generation
 |
 v
Evidence Verification
 |
 v
Quantitative RCA Ranking
```

## Evaluation Metrics

### RCA

- Top-1 Accuracy
- Top-3 Accuracy
- Mean Reciprocal Rank (MRR)

### Evidence

- Evidence Precision
- Evidence Recall
- Evidence Coverage
- Evidence Attribution Accuracy
- Contradiction Detection Rate

### Reliability

- Unsupported Claim Rate
- Invalid Evidence Citation Rate
- Contradiction Rate
- Structured Output Failure Rate

### Efficiency

- End-to-End Latency
- Preprocessing Time
- Number of LLM Calls
- Input Tokens
- Output Tokens
- Estimated Inference Cost
- Context Reduction Percentage

## Ablation Study

```text
A. Direct LLM
B. + Semantic Grouping
C. + Temporal Correlation
D. + Service Dependency Graph
E. + Evidence Verification
F. Full System
```

Expected result table:

| Configuration | Top-1 | Top-3 | MRR | Unsupported Claims | Tokens | Latency |
|---|---:|---:|---:|---:|---:|---:|
| Direct LLM | TBD | TBD | TBD | TBD | TBD | TBD |
| + Semantic | TBD | TBD | TBD | TBD | TBD | TBD |
| + Temporal | TBD | TBD | TBD | TBD | TBD | TBD |
| + Dependency | TBD | TBD | TBD | TBD | TBD | TBD |
| + Verification | TBD | TBD | TBD | TBD | TBD | TBD |
| Full System | TBD | TBD | TBD | TBD | TBD | TBD |

> Results must only be added after experiments are actually performed.

## Robustness Experiments

The system will be evaluated under controlled degradation:

1. Irrelevant noise
2. Duplicate events
3. Missing evidence
4. Contradictory evidence
5. Long-context incidents

## Datasets

Potential datasets:

- HDFS
- BGL
- Thunderbird
- Public microservice / incident RCA benchmarks

Dataset selection depends on whether the dataset supports the intended evaluation task and contains defensible labels.

Each dataset should have a dataset card containing:

```text
Dataset
Source
Number of logs
Number of incidents
Available labels
Root-cause labels
Log format
Known limitations
Preprocessing
Train/Validation/Test Split
```

> Root-cause ground truth must not be claimed unless supported by dataset documentation or a clearly documented annotation process.

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Embeddings | Sentence Transformers |
| NLP | Transformers |
| Graphs | NetworkX |
| LLM | OpenAI / compatible API / Local Model |
| API | FastAPI |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |
| Configuration | PyYAML, python-dotenv |
| Experiment Tracking | MLflow / Weights & Biases |
| CI | GitHub Actions |
| Version Control | Git / GitHub |

## Repository Structure

```text
LLM-Powered-Log-Triage/
|
+-- .github/
|   +-- workflows/
|   |   +-- pr-checks.yml
|   +-- pull_request_template.md
|
+-- data/
|   +-- raw/
|   +-- processed/
|   +-- sample/
|   +-- README.md
|
+-- configs/
|   +-- parser.yaml
|   +-- ranking.yaml
|   +-- experiments.yaml
|
+-- src/
|   +-- ingestion/
|   |   +-- log_loader.py
|   |
|   +-- preprocessing/
|   |   +-- log_preprocessor.py
|   |
|   +-- parsing/
|   |   +-- parser.py
|   |   +-- templates.py
|   |
|   +-- events/
|   |   +-- event_extractor.py
|   |
|   +-- grouping/
|   |   +-- semantic_cluster.py
|   |
|   +-- graphs/
|   |   +-- temporal_graph.py
|   |   +-- dependency_graph.py
|   |
|   +-- evidence/
|   |   +-- evidence_builder.py
|   |   +-- verifier.py
|   |
|   +-- llm/
|   |   +-- client.py
|   |   +-- prompts.py
|   |   +-- schemas.py
|   |
|   +-- ranking/
|   |   +-- rca_ranker.py
|   |
|   +-- timeline/
|   |   +-- timeline_generator.py
|   |
|   +-- pipeline/
|       +-- incident_pipeline.py
|
+-- app/
|   +-- app.py
|
+-- experiments/
|   +-- baselines/
|   +-- ablations/
|   +-- robustness/
|   +-- run_experiments.py
|
+-- evaluation/
|   +-- metrics.py
|   +-- evaluator.py
|   +-- result_analysis.py
|
+-- tests/
|   +-- test_preprocessing.py
|   +-- test_parsing.py
|   +-- test_grouping.py
|   +-- test_graphs.py
|   +-- test_evidence.py
|   +-- test_ranking.py
|   +-- test_timeline.py
|
+-- results/
|   +-- tables/
|   +-- figures/
|
+-- docs/
|   +-- dataset_card.md
|   +-- research_protocol.md
|
+-- requirements.txt
+-- pytest.ini
+-- README.md
+-- LICENSE
```

## Installation

### Clone

```bash
git clone https://github.com/priyanshu015211/LLM-Powered-Log-Triage.git
cd LLM-Powered-Log-Triage
```

### Create Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Create a `.env` file locally:

```env
LLM_API_KEY=your_api_key_here
LLM_MODEL=your_model_name
```

Never commit `.env` or API keys.

## Usage

Once the relevant modules are implemented:

```bash
python -m src.pipeline.incident_pipeline
```

Launch the dashboard:

```bash
streamlit run app/app.py
```

Run experiments:

```bash
python experiments/run_experiments.py
```

## Testing

Run:

```bash
python -m pytest -q
```

The test suite should eventually cover:

- preprocessing
- parsing
- event extraction
- semantic grouping
- temporal graphs
- dependency graphs
- evidence construction
- evidence verification
- RCA ranking
- timeline generation
- evaluation metrics

## Research Reproducibility

Every experiment should record:

```text
Dataset version
Dataset split
Random seed
Embedding model
LLM/model version
Prompt version
Ranking configuration
Temperature
Number of LLM calls
Token usage
Runtime
Hardware
Software environment
```

Store experiment results as machine-readable files:

```text
results/
+-- baseline_results.csv
+-- ablation_results.csv
+-- robustness_results.csv
+-- cost_results.csv
```

## Security and Privacy

Logs can contain sensitive operational information.

Never commit:

- Production logs
- API keys
- Passwords
- Authentication tokens
- Session cookies
- Personal identifiers
- Private infrastructure information

Recommended `.gitignore` entries:

```text
.env
.venv/
__pycache__/
*.pyc
data/raw/
results/private/
*.log
```

For public demonstrations, use synthetic or anonymized logs.

If external LLM APIs are used, document whether log content is transmitted externally.

## Team Structure

This is a four-member research project.

### Member 1 — Log Intelligence & Data

Responsible for:

- Dataset preparation
- Log ingestion
- Parsing
- Event extraction
- Embeddings
- Semantic clustering

### Member 2 — Temporal & Dependency Reasoning

Responsible for:

- Temporal event graph
- Service dependency graph
- Propagation analysis
- Temporal/dependency features

### Member 3 — LLM & Evidence Grounding

Responsible for:

- LLM integration
- Prompt engineering
- Structured output
- Evidence builder
- Evidence verification
- Contradiction analysis
- RCA ranking

### Member 4 — Evaluation & System

Responsible for:

- Baselines
- Evaluation framework
- Metrics
- Ablation experiments
- Robustness experiments
- Cost/latency analysis
- Dashboard
- Research visualizations

All team members contribute to research methodology, experimentation, analysis, documentation, and the final paper.

## 10-Week Development Plan

| Week | Main Milestone |
|---|---|
| 1 | Dataset, schema, research protocol |
| 2 | Parsing and event extraction |
| 3 | Embeddings and semantic grouping |
| 4 | Temporal and dependency graphs |
| 5 | Evidence builder |
| 6 | LLM hypothesis generation |
| 7 | Evidence verification and RCA ranking |
| 8 | Baselines and evaluation |
| 9 | Ablation and robustness experiments |
| 10 | Dashboard, results, paper, final integration |

## Development Roadmap

### Phase 1 — Foundation

- [ ] Improve parser
- [ ] Define common log schema
- [ ] Add ingestion
- [ ] Add unit tests

### Phase 2 — Event Intelligence

- [ ] Event extraction
- [ ] Embeddings
- [ ] Semantic clustering

### Phase 3 — Structured Relationships

- [ ] Temporal event graph
- [ ] Service dependency graph

### Phase 4 — Evidence-Grounded LLM

- [ ] LLM client
- [ ] Structured prompts
- [ ] JSON schema
- [ ] Hypothesis generation
- [ ] Evidence citation
- [ ] Evidence verification

### Phase 5 — Ranking

- [ ] Evidence scoring
- [ ] Contradiction penalty
- [ ] Candidate ranking

### Phase 6 — Interface

- [ ] Dashboard
- [ ] Timeline
- [ ] Evidence explorer

### Phase 7 — Research Evaluation

- [ ] Dataset experiments
- [ ] Baselines
- [ ] Metrics
- [ ] Ablation
- [ ] Robustness
- [ ] Cost/latency experiments

### Phase 8 — Paper

- [ ] Literature review
- [ ] Methodology
- [ ] Experimental results
- [ ] Error analysis
- [ ] Limitations
- [ ] Reproducibility package

## Contributing

Contributions are welcome through Pull Requests.

### Workflow

```text
Fork / Clone
     |
     v
Create Feature Branch
     |
     v
Implement Change
     |
     v
Run Tests
     |
     v
Create Pull Request
     |
     v
CI Checks
     |
     v
Code Review
     |
     v
Merge into main
```

Recommended branch names:

```text
feature/log-parsing
feature/event-extraction
feature/semantic-grouping
feature/temporal-graph
feature/evidence-verification
feature/rca-ranking
feature/evaluation
feature/dashboard
```

### Before Opening a PR

```bash
python -m pytest -q
```

Ensure:

- Tests pass
- No secrets are committed
- New functionality has tests
- Documentation is updated where required
- Research claims are supported by actual results

## Research Integrity

This project follows an experimental research methodology.

- Results are not predetermined.
- Metrics must be calculated from actual experiments.
- Failed experiments should not be hidden.
- Baselines should use comparable evaluation conditions.
- Ground-truth labels must come from documented sources or a clearly described annotation process.
- LLM-generated explanations must not automatically be treated as ground truth.
- Research claims must be supported by measured results.
- Illustrative scores must never be presented as experimental results.

## Current Status

> **Status: Research Prototype — In Development**

### Currently Implemented

- Basic Python project structure
- Log normalization
- Structured parsing for the initial log format
- Timestamp validation
- Pytest configuration
- Basic CI workflow
- Pull-request template

### Under Development

- [ ] Multi-format ingestion
- [ ] Event extraction
- [ ] Embedding pipeline
- [ ] Semantic clustering
- [ ] Temporal event graph
- [ ] Service dependency graph
- [ ] Evidence builder
- [ ] LLM integration
- [ ] Structured LLM output
- [ ] Evidence verification
- [ ] RCA scoring
- [ ] Timeline generation
- [ ] Dashboard
- [ ] Evaluation datasets
- [ ] Benchmark baselines
- [ ] Ablation experiments
- [ ] Robustness experiments
- [ ] Research metrics

> The repository should not claim research components as implemented until they are actually implemented and experimentally evaluated.

## Research Positioning

This project is positioned as:

> **A research framework for evaluating whether structured, evidence-grounded reasoning improves the reliability and efficiency of LLM-based root-cause analysis for distributed-system incidents.**

It is intentionally not positioned as:

> "An LLM that automatically finds the root cause."

The primary research contribution is the **evidence-grounded RCA methodology and its experimental evaluation**, while the dashboard serves as the demonstration and analysis interface.

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Evidence • Reasoning • Verification • Reproducibility</b>
</p>
