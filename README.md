# SuRaksha AI: Agentic Compliance Orchestrator

A 4-agent CrewAI system for automated regulatory compliance analysis and MAP (Mitigation Action Plan) generation for banking institutions.

## Overview

SuRaksha AI processes RBI circulars and other regulatory documents to:
- Extract regulatory clauses
- Generate actionable mitigation action points (MAPs)
- Audit MAPs against internal bank policies
- Dispatch approved tickets to IT departments

## Architecture

### Agents

1. **Regulatory Analyst** - Extracts and interprets regulatory text from PDF circulars
2. **MAP Architect** - Generates structured MAPs with confidence scores and explainability triggers
3. **Internal Auditor** - Audits MAPs against internal policies using RAG-based policy search
4. **IT Dispatcher** - Creates compliance tickets in the database after human approval

### Tools

- **PDF Reader** (`tools/pdf_reader.py`) - Extracts text from PDF documents using pypdf and pdfplumber
- **DB Manager** (`tools/db_manager.py`) - Manages SQLite database for compliance tickets and audit trails
- **Policy Search** (`tools/rag_memory.py`) - ChromaDB-based RAG system for searching internal policies

## Tech Stack

- **Python 3.11+**
- **CrewAI 1.14.4** - Multi-agent orchestration framework
- **Google Gemini** - LLM for agent reasoning (via `gemini-flash-latest` model)
- **ChromaDB** - Vector database for policy embeddings
- **Streamlit** - Web UI for human-in-the-loop approval workflow
- **SQLite** - Database for compliance tickets and audit trails
- **pdfplumber** - PDF text extraction with paragraph preservation
- **sentence-transformers** - Text embeddings for RAG

## Project Structure

```
suraksha_agentic_complianc/
├── agents/
│   ├── crew_logic.py          # ComplianceCrew class and pipeline orchestration
│   └── config/
│       ├── agents.yaml        # Agent configurations (role, goal, backstory)
│       └── tasks.yaml        # Task definitions and dependencies
├── tools/
│   ├── pdf_reader.py          # PDF text extraction tools
│   ├── db_manager.py          # Database management tools
│   └── rag_memory.py          # Policy search with ChromaDB
├── data/
│   └── base_policies.txt      # Internal bank policies for RAG
├── data_assets/
│   └── sample_rbi_circular.pdf # Sample RBI circular for testing
├── database/
│   ├── bank_policies.chroma   # ChromaDB vector database
│   └── compliance_tickets.db  # SQLite database for tickets
├── app.py                     # Streamlit dashboard
├── requirements.txt           # Python dependencies
└── .env                      # API keys (not in git)
```

## Setup

### Prerequisites

- Python 3.11+ (tested with 3.11.15)
- Google Gemini API key
- Homebrew (for Python installation on macOS)

### Installation

1. Clone the repository

2. Install Python 3.11 (if not already installed):
   ```bash
   brew install python@3.11
   ```

3. Create virtual environment:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install "crewai[google-genai]"  # Required for Google Gemini provider
   ```

5. Configure environment variables:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

### Running the Pipeline

**CLI Mode:**
```bash
python agents/crew_logic.py
```

**Streamlit Dashboard:**
```bash
streamlit run app.py
```

## Pipeline Execution

### Phase 1: Extraction & Audit (Automated)

1. Regulatory Analyst extracts text from uploaded PDF
2. MAP Architect generates structured MAPs with:
   - `map_id`: Unique identifier
   - `action_title`: Description of required action
   - `target_department`: Department responsible
   - `explainability_trigger`: Rationale for the MAP
   - `confidence_score`: AI confidence level (0-1)
3. Internal Auditor reviews MAPs against policies using RAG search

### Phase 2: Human Approval (HITL)

Streamlit dashboard displays:
- Pending MAPs with color-coded confidence scores
- Audit findings and policy references
- Approve/Revise interface for human review

### Phase 3: Execution (After Approval)

IT Dispatcher creates compliance tickets in SQLite database with:
- Task description
- Target department
- Explainability trigger
- Confidence score
- Timestamp

## Sample Output

```json
{
  "audit_results": [
    {
      "map_id": "MAP-001",
      "verdict": "REVISE",
      "confidence_score": 0.92,
      "issues": [
        {
          "issue_type": "WRONG_DEPT",
          "description": "CBS billing logic changes belong to Core Banking, not IT Security",
          "policy_reference": "Group IT Governance Policy v4.1, Section 2.3",
          "required_change": "Change target_department to IT_CORE_BANKING"
        }
      ]
    },
    {
      "map_id": "MAP-004",
      "verdict": "APPROVE",
      "confidence_score": 0.95,
      "issues": []
    }
  ],
  "total_maps": 9,
  "approved_count": 5,
  "revision_count": 4
}
```

## Configuration

### Agent Configuration (agents/config/agents.yaml)

Define agent roles, goals, and backstories. Each agent has:
- **Role**: Professional identity
- **Goal**: Primary objective
- **Backstory**: Context and epistemic standards

### Task Configuration (agents/config/tasks.yaml)

Define task execution flow with:
- **Description**: Task instructions with variable placeholders
- **Expected Output**: Schema for validation
- **Agent**: Assigned agent
- **Context**: Task dependencies

## Development

### Testing Tools

Test individual tools without CrewAI:
```bash
python test_tools.py
```

### List Available Gemini Models

```bash
python list_gemini_models.py
```

## License

MIT License

## Contributing

This project was developed for the SuRaksha AI hackathon.
