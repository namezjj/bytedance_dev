# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated evaluation agent system for dialogue models built on LangChain. It provides multi-dimensional evaluation (accuracy, relevance, completeness, fluency) of LLM responses using a judge LLM to evaluate responses from a model under test.

**Key Architecture Pattern**: The system uses a "judge + evaluated" model pattern where:
- **Judge LLM** (evaluator): Doubao by default - performs the evaluation
- **Evaluated LLM**: DeepSeek by default - the model being tested

## Common Commands

### Setup and Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Verify configuration (checks .env and project structure)
python test_setup.py
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_evaluation_agent.py

# Run with coverage
python -m pytest --cov=core tests/
```

### Running Examples
```bash
# Basic evaluation
python examples/basic_evaluation.py

# RAG system evaluation
python examples/rag_evaluation.py

# Doubao-DeepSeek evaluation
python examples/doubao_deepseek_evaluation.py

# Model comparison
python examples/model_comparison.py

# RAG system demo
python examples/rag_system_demo.py
```

## Configuration System

### Environment Variables (.env)

The system is configured via environment variables in `.env`:

**Doubao Configuration** (Judge LLM):
```bash
DOUBAO_API_KEY=your-api-key
DOUBAO_MODEL_NAME=ep-20250614210935-8mthr
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

**DeepSeek Configuration** (Evaluated LLM):
```bash
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**Evaluator Configuration** (Which LLM judges):
```bash
EVALUATOR_PROVIDER=doubao
EVALUATOR_MODEL_NAME=ep-20250614210935-8mthr
EVALUATOR_API_KEY=your-doubao-key
```

**Evaluated Model Configuration** (Which LLM is tested):
```bash
EVALUATED_PROVIDER=deepseek
EVALUATED_MODEL_NAME=deepseek-chat
EVALUATED_API_KEY=your-deepseek-key
```

### Configuration Templates

The system provides predefined configuration templates in `config/evaluation_config.py`:
- `quick_eval` - Fast evaluation
- `comprehensive_eval` - Full evaluation
- `accuracy_focused` - Focus on accuracy
- `performance_optimized` - Optimized for speed
- `development` - Dev environment
- `production` - Production environment

## Core Architecture

### LLM Provider System (`core/llm_providers/`)

All LLM integrations follow a unified provider pattern:

- `base_provider.py` - Abstract base class with `acall()` async interface
- `doubao_provider.py` - Doubao (Bytedance) implementation
- `deepseek_provider.py` - DeepSeek implementation
- `provider_factory.py` - Factory for creating providers

**Key Design**:
- All providers implement `BaseLLMProvider` with async `acall()` method
- Built-in retry mechanism with exponential backoff
- Automatic latency and token usage tracking
- Returns `LLMResponse` dataclass with text, usage, latency, metadata

**Creating LLM instances**:
```python
from core.llm_providers import LLMProviderFactory

# Auto-create from environment variables
evaluator = LLMProviderFactory.create_evaluator_llm()
evaluated = LLMProviderFactory.create_evaluated_llm()

# Manual creation
llm = LLMProviderFactory.create(
    provider_name="doubao",
    api_key="...",
    model_name="..."
)
```

### Evaluation Agent (`core/evaluation_agent.py`)

The `EvaluationAgent` class orchestrates the evaluation process:

**Input**: `EvaluationInput` dataclass with:
- `question` - The question asked
- `ground_truth` - Optional reference answer
- `context` - Optional context
- `conversation_history` - Optional chat history
- `metadata` - Optional metadata

**Output**: `EvaluationResult` with:
- `overall_score` - Weighted average score
- `dimension_scores` - Dict of scores per dimension
- `detailed_feedback` - Dict of feedback per dimension
- `evaluation_timestamp`
- `metadata`

**Evaluation Modes**:
- `SINGLE` - Evaluate one response
- `BATCH` - Evaluate multiple responses
- `COMPARATIVE` - Compare multiple models

### Evaluators (`core/evaluators/`)

Each dimension has its own evaluator inheriting from `BaseEvaluator`:

- `accuracy_evaluator.py` - Factual correctness
- `relevance_evaluator.py` - Question relevance
- `completeness_evaluator.py` - Information completeness
- `fluency_evaluator.py` - Language fluency

All evaluators implement:
- `get_dimension_name()` - Returns dimension name
- `_get_evaluation_prompt()` - Returns LLM prompt for this dimension
- `evaluate(evaluation_input, model_response)` - Performs evaluation

### RAG System (`core/rag_system.py`)

A complete RAG implementation with:
- Vector database integration (supports multiple backends)
- Document chunking and embedding
- Retrieval and answer generation
- Built-in evaluation integration

### Data Management (`data/`)

- `database.py` - SQLite database operations for storing evaluation results
- `models.py` - Data models and schemas

### Reporting (`reporting/`)

- `report_generator.py` - Generate HTML/JSON/PDF reports
- `visualizer.py` - Create charts (radar plots, distributions, trends, heatmaps)

## Adding New LLM Providers

To add a new provider:

1. Create provider class in `core/llm_providers/`:
```python
from .base_provider import BaseLLMProvider, LLMResponse

class NewProvider(BaseLLMProvider):
    def get_provider_name(self) -> str:
        return "new_provider"

    async def acall(self, prompt, temperature=0.7, max_tokens=2000, **kwargs):
        # Implement API call logic
        # Return LLMResponse instance
        pass
```

2. Register in `provider_factory.py`:
```python
_providers = {
    "doubao": DoubaoProvider,
    "deepseek": DeepSeekProvider,
    "new_provider": NewProvider,  # Add here
}
```

3. Add environment variables and factory methods as needed

## Adding Custom Evaluators

```python
from core.evaluators.base_evaluator import BaseEvaluator

class CustomEvaluator(BaseEvaluator):
    def get_dimension_name(self):
        return "custom_dimension"

    def _get_evaluation_prompt(self):
        return """Your evaluation prompt..."""

    async def evaluate(self, evaluation_input, model_response):
        score, feedback = await self._call_llm(prompt)
        return score, feedback

# Register with agent
agent.evaluators['custom'] = CustomEvaluator(agent.llm, agent.config)
```

## Important Implementation Details

### Async-First Design
All LLM calls are async. Use `asyncio.run()` for top-level execution:
```python
import asyncio

async def main():
    result = await agent.evaluate_single(input, response)

asyncio.run(main())
```

### Configuration Loading
Config is loaded in this order (later overrides earlier):
1. Default values in `EvaluationConfig` dataclass
2. Configuration template (if specified)
3. Environment variables
4. Explicit parameters passed to constructors

### Weight Normalization
Dimension weights are automatically normalized to sum to 1.0 when calculating `overall_score`.

### Database Schema
Evaluation results are stored in SQLite with schema defined in `data/models.py`. The database supports:
- Storing individual evaluation results
- Querying by model, date range, score range
- Tracking trends over time
- Generating comparison reports

## Python Version

Requires Python 3.8+

## Key Dependencies

- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP client for LLM APIs
- `pandas`, `numpy` - Data processing
- `matplotlib`, `plotly`, `seaborn` - Visualization
- `sqlalchemy` - Database ORM
- `optuna` - Hyperparameter optimization
- `pytest`, `pytest-asyncio` - Testing
