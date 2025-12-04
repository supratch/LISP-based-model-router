# ⚡ Priority Setting in Query Routing - Explanation

## What is Priority?

The **Priority** setting in the Query Routing Interface determines how urgently your query should be processed and influences which model is selected for routing.

---

## 🎯 Priority Levels

There are **three priority levels** available:

| Priority | Description | Use Case | Score Multiplier |
|----------|-------------|----------|------------------|
| **Low** | Best effort, may use slower models | Non-urgent queries, batch processing | 0.9x |
| **Medium** | Balanced performance (default) | Standard queries, general use | 1.0x |
| **High** | Fastest available model, priority processing | Urgent queries, time-sensitive requests | 1.1x |

---

## 📊 How Priority Affects Routing

### 1. **Model Selection Score**

Priority directly affects the routing score calculation:

<augment_code_snippet path="backend/app/models/llm_router.py" mode="EXCERPT">
````python
# Adjust for query complexity and priority
if analysis.is_complex and capability == ModelCapability.EXCELLENT:
    total_score *= 1.2

if analysis.priority == "high":
    total_score *= 1.1  # 10% boost
elif analysis.priority == "low":
    total_score *= 0.9  # 10% penalty
````
</augment_code_snippet>

### 2. **Automatic Priority Detection**

The system can automatically determine priority based on:

<augment_code_snippet path="backend/app/models/llm_router.py" mode="EXCERPT">
````python
def _determine_priority(self, query: str, context: Dict) -> str:
    """Determine query priority based on content and context."""
    # Check for priority indicators in context
    if context.get("urgent", False) or context.get("priority", "").lower() == "high":
        return "high"
    
    # Check for priority keywords in query
    priority_keywords = ['urgent', 'immediately', 'asap', 'critical']
    if any(keyword in query.lower() for keyword in priority_keywords):
        return "high"
    
    # Short queries are typically low priority
    if len(query.split()) < 10:
        return "low"
    
    return "medium"
````
</augment_code_snippet>

---

## 🔄 Priority in Action

### Example 1: High Priority Query

**Input:**
- Query: "Urgent: Generate code for authentication system"
- Priority: High
- Complexity: Medium

**Effect:**
- Model selection score boosted by **10%**
- Faster models preferred
- Lower latency prioritized over cost

**Result:**
- Selected Model: `phi3-local` (fast code generation)
- Estimated Response Time: 1.2s
- Confidence: 95%

---

### Example 2: Low Priority Query

**Input:**
- Query: "What is AI?"
- Priority: Low
- Complexity: Low

**Effect:**
- Model selection score reduced by **10%**
- Cost-effective models preferred
- May use models with higher latency

**Result:**
- Selected Model: `llama3.2-local` (cost-effective)
- Estimated Response Time: 2.5s
- Confidence: 88%

---

### Example 3: Medium Priority Query (Default)

**Input:**
- Query: "Explain machine learning algorithms in detail"
- Priority: Medium
- Complexity: High

**Effect:**
- No score adjustment (1.0x multiplier)
- Balanced selection based on capabilities
- Considers all factors equally

**Result:**
- Selected Model: `llama3.2-local` (best for reasoning)
- Estimated Response Time: 1.8s
- Confidence: 92%

---

## 🧮 Routing Score Calculation

The total routing score is calculated using multiple factors:

```
Total Score = (
    Capability Score × 0.4 +
    Load Score × 0.3 +
    Cost Score × 0.2 +
    Response Time Score × 0.1
) × Priority Multiplier × Complexity Multiplier
```

### Priority Multipliers:
- **High**: 1.1 (10% boost)
- **Medium**: 1.0 (no change)
- **Low**: 0.9 (10% reduction)

---

## 💡 When to Use Each Priority

### Use **HIGH Priority** When:
- ✅ Time-sensitive requests
- ✅ Real-time applications
- ✅ User is waiting for immediate response
- ✅ Critical business operations
- ✅ Query contains urgent keywords

**Examples:**
- "Urgent: Debug this production error"
- "Immediately generate API documentation"
- "Critical: Analyze security vulnerability"

---

### Use **MEDIUM Priority** When:
- ✅ Standard queries (default)
- ✅ General information requests
- ✅ Balanced performance needed
- ✅ No specific urgency

**Examples:**
- "Explain machine learning"
- "Write a Python function to sort data"
- "What are the benefits of cloud computing?"

---

### Use **LOW Priority** When:
- ✅ Batch processing
- ✅ Non-urgent queries
- ✅ Cost optimization is important
- ✅ Background tasks
- ✅ Simple queries

**Examples:**
- "What is AI?"
- "Define recursion"
- "List programming languages"

---

## 🎨 UI Location

In the **Query Routing Interface**:

```
┌─────────────────────────────────┐
│ Query Text Box                  │
│ (Enter your query here)         │
└─────────────────────────────────┘

Priority: [Medium ▼]  ← Dropdown selector
          ├─ Low
          ├─ Medium (default)
          └─ High

Source EID: [10.1.0.1]

[Route Query Button]
```

---

## 📈 Impact on Performance

### High Priority:
- ⚡ **Faster response times** (10-20% improvement)
- 💰 **May cost more** (uses premium models)
- 🎯 **Higher confidence** in model selection
- 📊 **Better resource allocation**

### Medium Priority:
- ⚖️ **Balanced performance**
- 💵 **Moderate cost**
- 🎯 **Standard confidence**
- 📊 **Normal resource allocation**

### Low Priority:
- 🐌 **Slower response times** (acceptable)
- 💰 **Lower cost** (uses efficient models)
- 🎯 **Adequate confidence**
- 📊 **Minimal resource usage**

---

## 🔍 Priority in Routing Metadata

After routing, you can see how priority affected the decision:

```json
{
  "routing_metadata": {
    "query_analysis": {
      "priority": "high",
      "complexity_score": 0.75,
      "estimated_tokens": 150
    }
  },
  "selected_model": "phi3-local",
  "confidence_score": 0.95,
  "reasoning": "Selected Phi-3 for high-priority code generation..."
}
```

---

## 🚀 Best Practices

1. **Use Default (Medium)** for most queries
2. **Reserve High Priority** for truly urgent requests
3. **Use Low Priority** for batch jobs or simple queries
4. **Let Auto-Detection Work** - system detects urgent keywords
5. **Monitor Costs** - high priority may increase costs

---

## 📝 API Usage

When calling the API directly:

```bash
curl -X POST "http://localhost:8000/api/v1/route" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain machine learning",
    "priority": "high",
    "source_eid": "10.1.0.1"
  }'
```

---

## 🎯 Summary

| Aspect | Low | Medium | High |
|--------|-----|--------|------|
| **Speed** | Slower | Balanced | Fastest |
| **Cost** | Lowest | Moderate | Highest |
| **Score Multiplier** | 0.9x | 1.0x | 1.1x |
| **Use Case** | Batch | Standard | Urgent |
| **Default** | No | **Yes** | No |

**Default Priority**: Medium (if not specified)

---

**Pro Tip**: The system automatically detects urgent keywords like "urgent", "immediately", "asap", "critical" and sets priority to HIGH automatically!

