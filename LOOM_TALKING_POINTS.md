# Project Samarth - Plugin Architecture - Loom Video Script (2 minutes)

## Opening (15 seconds)
"Hi! I'm presenting Project Samarth with Plugin Architecture - a highly extensible Q&A system over India's agricultural and climate data from data.gov.in. This version demonstrates the power of modular, plugin-based design."

## Architecture Choice: Why Plugin Pattern? (25 seconds)

**The Challenge:**
Traditional monolithic analytics systems become unmaintainable as query types grow. Adding new features requires modifying core code, risking regressions.

**The Solution: Self-Registering Plugin System**
- Each query type is an independent plugin
- Plugins auto-register using Python decorators
- QueryEngine dynamically discovers and routes to plugins
- Zero coupling between plugins - test and deploy independently

**Show Diagram:**
```
QueryEngine (Registry) → Routes to → [Plugin 1] [Plugin 2] [Plugin 3] [Plugin 4]
                                     Compare    Districts  Trends    Policy
```

## Key Architecture Components (30 seconds)

### 1. Plugin Registration System (`app/query_engine.py`)
```python
@QueryEngine.register("compare_rainfall_and_crops")
def compare_plugin(params, datasets):
    # Independent analysis logic
    return results
```

**Why this matters:**
- **Decorator pattern** → Automatic discovery
- **No central switch statement** → Clean routing
- **Each plugin is a function** → Simple, testable

### 2. Plugin Structure (`app/plugins/`)
```
plugins/
├── compare_rainfall_crops.py      # Plugin 1
├── district_extremes.py           # Plugin 2
├── production_trend.py            # Plugin 3
└── policy_arguments.py            # Plugin 4
```

**Show code snippet:**
Open `app/plugins/compare_rainfall_crops.py` - highlight:
- Import decorator
- Register with intent name
- Self-contained logic
- Returns standardized format

### 3. Benefits Over Monolithic Design
✅ **Add new query types** → Create new file, no core changes
✅ **Test in isolation** → Each plugin has own unit tests
✅ **Deploy independently** → Plugins can be hot-swapped
✅ **Clear ownership** → Each teammate owns specific plugins

## Live Demo (35 seconds)

**[Show terminal + browser side by side]**

1. **Start Server:**
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

2. **Test Query 1:** "Compare rainfall in Kerala and Punjab over 3 years"
   - **Show:** Plugin registry logs `compare_rainfall_and_crops` plugin executing
   - **Result:** Rainfall table + crop rankings
   - **Point out:** Debug field shows which plugin handled it

3. **Test Query 2:** "Which district in Punjab had highest wheat production in 2020?"
   - **Show:** Different plugin (`district_extremes`) handles this
   - **Result:** District-level extremes table
   - **Highlight:** Same engine, different plugin, zero coupling

4. **Show Plugin Discovery:**
```bash
curl http://localhost:8001/health
# In logs: See "4 plugins registered"
```

## Adding a New Plugin - Live Code (20 seconds)

**Show how easy it is to extend:**

Create `app/plugins/seasonal_analysis.py`:
```python
from ..query_engine import QueryEngine

@QueryEngine.register("seasonal_patterns")
def seasonal_plugin(params, datasets):
    # New analysis logic here
    return {"answer": "...", "tables": [...], "citations": [...]}
```

**That's it!** Plugin automatically:
- Registers with QueryEngine
- Gets routed by intent parser
- Executes independently

No changes to `main.py`, `query_engine.py`, or other plugins.

## Technical Highlights (15 seconds)

**Code Quality:**
- Type hints throughout
- Decorator-based registration
- Standardized plugin interface
- Data.gov.in API integration with caching
- Graceful fallback to local data

**Architecture Patterns:**
1. **Plugin Pattern** - Extensible query handlers
2. **Registry Pattern** - Central plugin discovery
3. **Strategy Pattern** - Runtime algorithm selection
4. **Template Method** - Standardized plugin interface

## Comparison to Other Architectures (10 seconds)

| Architecture | Add Feature | Coupling | Testing |
|--------------|-------------|----------|---------|
| Monolithic | Modify core | High | Complex |
| **Plugin** | New file | None | Isolated |
| Event-Driven | New stage | Low | Moderate |

**Plugin wins when:** You need maximum modularity and independent feature deployment.

## Closing (5 seconds)
"This plugin architecture demonstrates enterprise-grade extensibility. Add unlimited query types without ever touching core code. Perfect for teams where different developers own different features. Thank you!"

---

## Demo Checklist

**Preparation:**
- [ ] Server running on port 8001
- [ ] Browser ready with test queries
- [ ] Terminal showing logs
- [ ] Code editor with plugin file open

**Show During Demo:**
- [ ] Plugin registry in logs (4 plugins registered)
- [ ] Different plugins handling different queries
- [ ] Plugin file structure in `/app/plugins`
- [ ] Decorator registration syntax
- [ ] Debug output showing plugin name

**Code to Highlight:**
- [ ] `@QueryEngine.register()` decorator
- [ ] Plugin directory structure
- [ ] Standardized return format
- [ ] Zero imports between plugins

## Key Differentiators to Emphasize

1. **Self-Registration:** Plugins discover themselves via decorators
2. **Zero Coupling:** Plugins don't know about each other
3. **Hot-Swappable:** Add/remove plugins without restart (with reload)
4. **Team Scalability:** Each dev can own specific plugins
5. **Testing Simplicity:** Unit test each plugin independently
6. **Production Pattern:** Used by major systems (Kubernetes, WordPress, VS Code)
