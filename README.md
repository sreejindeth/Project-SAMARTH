# Project Samarth - Plugin Architecture

A flexible, extensible data analysis API built with **Plugin Architecture** pattern for analyzing Indian agriculture and rainfall data from data.gov.in.

## Architecture Highlights

### Plugin-Based Design

This project uses a **self-registering plugin architecture** that makes it easy to add new query types without modifying the core system.

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
├─────────────────────────────────────────────────────────┤
│                      QueryEngine                         │
│           (Centralized Plugin Registry)                  │
├─────────────────────────────────────────────────────────┤
│  Plugin 1        Plugin 2        Plugin 3    Plugin 4   │
│  Compare         District        Production  Policy      │
│  Rainfall        Extremes        Trends      Arguments   │
└─────────────────────────────────────────────────────────┘
```

### Key Architectural Benefits

- **Loose Coupling**: Plugins are independent modules
- **Easy Extension**: Add new query types by creating new plugin files
- **Self-Registration**: Plugins automatically register with the QueryEngine via decorators
- **Centralized Routing**: QueryEngine handles all plugin discovery and execution

### How It Works

1. **Plugin Registration**: Each plugin uses the `@QueryEngine.register()` decorator
2. **Intent Matching**: QueryEngine routes queries based on parsed intent
3. **Execution**: Matched plugin executes analysis
4. **Formatting**: Plugin returns formatted results

## Project Structure

```
project-samarth-plugin/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── query_engine.py         # Plugin registry & router
│   │   ├── question_parser.py      # NLP intent parser
│   │   ├── data_manager.py         # Data.gov.in API client
│   │   ├── config.py               # Configuration
│   │   └── plugins/
│   │       ├── __init__.py         # Auto-loads all plugins
│   │       ├── compare_rainfall_crops.py
│   │       ├── district_extremes.py
│   │       ├── production_trend.py
│   │       └── policy_arguments.py
│   └── requirements.txt
└── README.md
```

## Features

- **4 Analysis Types** (each as a separate plugin):
  - Compare rainfall and top crops between states
  - Find district-level production extremes
  - Analyze production trends with climate correlation
  - Generate policy arguments for crop shifts

- **Real-time Data**: Fetches latest data from data.gov.in API
- **Caching**: In-memory data cache for performance
- **Natural Language**: Understands plain English queries

## Setup Instructions

### Prerequisites

- **Python 3.12** (Required - pandas 2.1.4 incompatible with Python 3.14)
- data.gov.in API key

### Installation

```bash
# Navigate to backend folder
cd backend

# Create virtual environment with Python 3.12
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Set your data.gov.in API key:

```bash
export DATAGOV_API_KEY=your_api_key_here
```

### Run the Server

```bash
uvicorn app.main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`

## API Endpoints

### Health Check
```bash
GET /health
```

Response:
```json
{"status": "ok"}
```

### Query Endpoint
```bash
POST /ask
Content-Type: application/json

{
  "question": "Compare rainfall in Kerala and Punjab over 3 years"
}
```

Response:
```json
{
  "answer": "Compared rainfall for Kerala and Punjab over 3 year(s). Kerala averaged 3050.0 mm while Punjab averaged 683.3 mm.",
  "tables": [
    {
      "title": "Average annual rainfall (mm)",
      "headers": ["Year", "Kerala", "Punjab"],
      "rows": [[2020, 3100.0, 710.0], [2021, 3000.0, 650.0], [2022, 3050.0, 690.0]]
    }
  ],
  "citations": [...],
  "debug": {
    "intent": "compare_rainfall_and_crops",
    "plugin": "compare_rainfall_and_crops",
    "params": {...}
  }
}
```

### Refresh Data
```bash
POST /refresh
```

Clears cache and fetches fresh data from data.gov.in

## Example Queries

```
"Compare rainfall in Kerala and Punjab over 3 years"
"Which district in Punjab had the highest wheat production in 2020?"
"Show rice production trend in Tamil Nadu over 5 years"
"Why should Karnataka shift from cotton to sugarcane?"
```

## Adding a New Plugin

Create a new file in `app/plugins/your_plugin.py`:

```python
from ..query_engine import QueryEngine

@QueryEngine.register("your_intent_name")
def your_plugin_handler(params: dict, datasets: dict) -> dict:
    """
    Handle your custom query type.

    Args:
        params: Parsed query parameters
        datasets: Dictionary of loaded dataframes

    Returns:
        Dictionary with 'answer', 'tables', 'citations'
    """
    # Your analysis logic here

    return {
        "answer": "Your answer text",
        "tables": [...],
        "citations": [...]
    }
```

The plugin automatically registers when the module loads!

## Technology Stack

- **FastAPI**: Modern async web framework
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **Uvicorn**: ASGI server
- **Python 3.12**: Runtime environment

## Data Sources

- **Agriculture**: District-wise crop production statistics
  - Source: https://data.gov.in/resources/district-wise-crop-production-statistics

- **Rainfall**: Sub-division wise rainfall distribution
  - Source: https://data.gov.in/resources/rainfall-sub-division-wise-distribution

## Architecture Advantages

### Scalability
- Add unlimited plugins without modifying core code
- Each plugin is isolated and testable

### Maintainability
- Clear separation of concerns
- Easy to locate and update specific functionality

### Flexibility
- Plugins can be enabled/disabled independently
- Easy to swap implementations

## License

This project is part of the Project Samarth prototype series.
