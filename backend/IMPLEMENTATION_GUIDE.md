# Project Samarth - Plugin Architecture Implementation Guide

## 🎯 What You Need to Complete

This scaffold demonstrates the **Plugin Architecture** pattern. I've created the core architecture - you need to implement the query logic for 4 plugins.

### ✅ Already Done (Core Architecture):
- ✅ Plugin base class and registry system (`app/core/plugin_base.py`)
- ✅ Core query engine (`app/core/engine.py`)
- ✅ Example plugin with structure (`app/plugins/compare_rainfall_crops_plugin.py`)
- ✅ Data manager (reused from Project 1)
- ✅ Question parser (reused from Project 1)

### 🔨 What YOU Need to Implement:

#### 1. Complete the Example Plugin (20 minutes)

Open `app/plugins/compare_rainfall_crops_plugin.py` and complete the `execute()` method.

**TODO sections marked in code:**
```python
# TODO: Implement rainfall comparison
# TODO: Implement crop ranking
# TODO: Generate answer text
# TODO: Create data tables
```

**Reference:** Copy logic from Project 1's `analytics.py` → `compare_rainfall_and_crops()` method.

**Sample Prompt for THIS plugin:**
```
Compare average rainfall in Punjab and Tamil Nadu over last 5 years.
Show top 3 Rice producing districts in each state.
```

#### 2. Create 3 More Plugins (1 hour)

Follow the same pattern as `compare_rainfall_crops_plugin.py`:

**Plugin 2: District Extremes**
- File: `app/plugins/district_extremes_plugin.py`
- Intent: `"district_extremes"`
- Sample Prompt: "Which districts in Karnataka and Kerala had highest and lowest Sugarcane production in 2020?"
- Reference: Project 1's `district_extremes()` method

**Plugin 3: Production Trend**
- File: `app/plugins/production_trend_plugin.py`
- Intent: `"production_trend_with_climate"`
- Sample Prompt: "Analyze Paddy production trend in Maharashtra for last 5 years and its correlation with monsoon patterns."
- Reference: Project 1's `production_trend_with_climate()` method

**Plugin 4: Policy Arguments**
- File: `app/plugins/policy_arguments_plugin.py`
- Intent: `"policy_arguments"`
- Sample Prompt: "Should we shift from Cotton to Maize in Karnataka? Provide data-driven policy arguments."
- Reference: Project 1's `policy_arguments()` method

#### 3. Update main.py (10 minutes)

Replace the analytics engine with plugin engine:

```python
# OLD (Project 1):
from .analytics import AnalyticsEngine
analytics = AnalyticsEngine(data_manager)

# NEW (Project 2 - Plugin Architecture):
from .core import QueryEngine
from . import plugins  # Triggers plugin registration
engine = QueryEngine(data_manager)

# In /ask endpoint:
result = engine.execute_query(parsed.intent, parsed.params)
```

#### 4. Update Sample Data (15 minutes)

Add states/crops needed for new prompts:
- Punjab: Rice, Wheat, Maize (already exists)
- Tamil Nadu: Rice, Sugarcane (add Sugarcane)
- Kerala: Sugarcane (add)
- Karnataka: Cotton (add)

Edit `backend/data/sample_agriculture.csv` to add missing crop data.

#### 5. Test (10 minutes)

```bash
cd backend
python test_prompts.py
```

Should see: **100% success rate (4/4 prompts)**

---

## 🏗️ Architecture Highlights (Explain in Loom)

### Plugin Registry Pattern
```python
# Plugins auto-register themselves:
plugin_registry.register(CompareRainfallCropsPlugin())

# Engine discovers plugins dynamically:
plugin = registry.find_plugin_for_params(intent, params)
```

**Benefits:**
- Add new query types without modifying core engine
- Each plugin is independent and testable
- Clean separation of concerns

### Strategy Pattern
Engine delegates to plugins based on intent - doesn't know implementation details.

### Template Method Pattern
Base class defines workflow, plugins implement specific logic.

---

## 📝 Completion Checklist

- [ ] Complete `compare_rainfall_crops_plugin.py` execute() method
- [ ] Create `district_extremes_plugin.py`
- [ ] Create `production_trend_plugin.py`
- [ ] Create `policy_arguments_plugin.py`
- [ ] Update `app/plugins/__init__.py` imports
- [ ] Update `main.py` to use QueryEngine
- [ ] Add missing states/crops to sample data
- [ ] Update frontend with 4 new sample prompts
- [ ] Run tests - achieve 100% pass rate
- [ ] Update README with architecture diagram
- [ ] Deploy to Render + Netlify
- [ ] Record Loom video

**Estimated Time:** 2-3 hours

---

## 🎬 Loom Video Talking Points

**Highlight these architectural decisions:**

1. **Plugin Architecture** - "Each question type is a separate plugin class"
2. **Dynamic Registration** - "Plugins register themselves, engine discovers them at runtime"
3. **Strategy Pattern** - "Engine delegates to plugins without knowing implementation"
4. **Extensibility** - "Adding new query types doesn't require changing core code"
5. **Comparison to Project 1** - "Original used monolithic analytics class, this uses modular plugins"

**Demo:**
- Show plugin registry listing available queries
- Execute a query and explain the flow: Parser → Engine → Plugin → Result
- Show how easy it is to add a new plugin

---

## 🆘 Need Help?

**Stuck on plugin implementation?**
- Reference Project 1's `analytics.py` - it has all the logic
- Each plugin method is ~50-100 lines
- Copy-paste is OK, but understand the flow!

**Architecture questions?**
- Review `core/plugin_base.py` - it's well-commented
- Plugin pattern is: validate params → load data → analyze → format result

Good luck! This architecture showcases advanced design patterns. 🚀
