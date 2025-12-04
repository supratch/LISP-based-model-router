# 🎯 Query Routing Interface - User Guide

## Overview

The Query Routing Interface now provides **complete end-to-end visibility** from query submission to LLM response generation.

---

## 🖥️ Interface Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Query Routing Interface                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LEFT PANEL: Query Input              RIGHT PANEL: Results         │
│  ┌─────────────────────────┐          ┌─────────────────────────┐ │
│  │ Query Text Box          │          │ 🤖 Generated Response   │ │
│  │ (Multi-line)            │          │ ┌─────────────────────┐ │ │
│  │                         │          │ │ [LLM Response Text] │ │ │
│  │                         │          │ │                     │ │ │
│  └─────────────────────────┘          │ │ Generation: 2.34s   │ │ │
│                                       │ └─────────────────────┘ │ │
│  Priority: [Medium ▼]                 │                         │ │
│  Source EID: [10.1.0.1]               │ 📊 Routing Result       │ │
│  Preferred Model: [Optional]          │ • Model: llama3.2-local │ │
│                                       │ • Method: LISP + DNS    │ │
│  [Route Query Button]                 │ • Confidence: 92%       │ │
│                                       │ • Endpoint: 127.0.0.1   │ │
│                                       │                         │ │
│                                       │ 🔍 Technical Details    │ │
│                                       │ [Expandable Accordion]  │ │
│                                       └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Usage

### 1. Enter Your Query

**Location**: Left panel, top text box

**Example Queries**:
- "Explain machine learning in simple terms"
- "Write a Python function to sort a list"
- "What is the capital of France?"
- "Generate a creative story about space exploration"

**Tips**:
- Be specific for better routing
- Longer queries get better model selection
- Code queries → routed to Phi-3
- Creative queries → routed to Llama 3.2

---

### 2. Configure Options

**Priority** (Dropdown):
- `Low` - Best effort, may use slower models
- `Medium` - Balanced performance (default)
- `High` - Fastest available model

**Source EID** (Text field):
- Default: `10.1.0.1`
- Represents your logical network identity
- Used for LISP routing decisions

**Preferred Model** (Optional):
- Leave blank for automatic selection
- Or specify: `llama3.2-local`, `phi3-local`, etc.

---

### 3. Submit Query

Click the **"Route Query"** button

**What Happens**:
1. ⏳ Button shows "Routing..." with spinner
2. 🔄 Backend performs routing analysis
3. 🤖 Selected model generates response
4. ✅ Results appear in right panel

**Timing**:
- Routing decision: ~50-200ms
- LLM generation: 1-5 seconds (depends on query)
- Total: Usually 2-6 seconds

---

## 📊 Understanding the Results

### Section 1: Generated Response (NEW! ✨)

```
┌─────────────────────────────────────────────────────┐
│ 🤖 Generated Response from llama3.2-local          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Machine learning is a subset of artificial        │
│  intelligence that enables computers to learn      │
│  from data without being explicitly programmed.    │
│  It uses algorithms to identify patterns and       │
│  make predictions or decisions based on that       │
│  data...                                           │
│                                                     │
│  Generation time: 2.34s                            │
└─────────────────────────────────────────────────────┘
```

**Features**:
- ✅ Shows actual LLM-generated text
- ✅ Displays which model generated it
- ✅ Shows generation time
- ✅ Scrollable for long responses
- ✅ Monospace font for readability

---

### Section 2: Routing Result Cards

Three cards showing key metrics:

**Card 1: Selected Model**
```
┌─────────────────┐
│   🧠 Model      │
│ llama3.2-local  │
│ Selected Model  │
└─────────────────┘
```

**Card 2: Routing Method**
```
┌─────────────────┐
│   🔀 Router     │
│  LISP + DNS     │
│ Routing Method  │
└─────────────────┘
```

**Card 3: Response Time**
```
┌─────────────────┐
│   ⚡ Speed      │
│     1.20s       │
│ Est. Response   │
└─────────────────┘
```

---

### Section 3: Routing Details

**Confidence Score**:
- 🟢 Green (80-100%): High confidence
- 🟡 Yellow (60-79%): Medium confidence
- 🔴 Red (<60%): Low confidence

**Endpoint**: Physical server address (RLOC)
- `127.0.0.1` = Local model
- `192.168.x.x` = Remote server

**Estimated Cost**: Per-query cost
- `$0.000000` = Free (local models)
- `$0.00003` = Paid API (GPT-4, Claude)

**Reasoning**: Why this model was selected
- Example: "Selected Llama 3.2 for general query with good reasoning capabilities"

---

### Section 4: Alternative Models

Shows other models that could handle the query:

```
Alternative Models:
[phi3-local] [gpt-4] [claude-3]
```

Click to see why they weren't selected.

---

### Section 5: Technical Metadata (Expandable)

Click to expand and see:

**Query Analysis**:
- Query type (e.g., "SIMPLE_QA", "CODE_GENERATION")
- Complexity score
- Estimated tokens
- Language detected

**LISP Routing**:
- Source EID → Destination EID mapping
- RLOC addresses
- Packet ID
- Instance ID

**DNS Routing**:
- Service name
- DNS record used
- Address and port

**Performance**:
- Processing time in milliseconds

---

## 🎨 Visual Indicators

### Loading State
```
[Routing... ⏳]
```
- Button disabled
- Spinner animation
- Previous results cleared

### Success State
```
✅ Results displayed
🤖 Response generated
📊 Metrics shown
```

### Error State
```
❌ Error: [Error message]
```
- Red alert box
- Descriptive error message
- Suggestions for resolution

---

## 💡 Tips & Best Practices

### For Best Results

1. **Be Specific**: "Write a Python function to sort" → Better than "code"
2. **Use Context**: Include relevant details in your query
3. **Check Model**: See which model was selected and why
4. **Review Response**: Verify the generated answer makes sense

### Model Selection Guide

| Query Type | Best Model | Why |
|------------|------------|-----|
| Code generation | `phi3-local` | Optimized for code |
| Math problems | `phi3-local` | Excellent at math |
| Creative writing | `llama3.2-local` | Better creativity |
| General Q&A | `llama3.2-local` | Balanced performance |
| Complex reasoning | `llama3.2-local` | Better reasoning |

---

## 🔧 Troubleshooting

### No Response Generated

**Symptom**: Error message instead of response

**Check**:
1. Is Ollama running? `curl http://localhost:11434/api/tags`
2. Are models installed? `ollama list`
3. Check backend logs for errors

### Slow Response

**Symptom**: Takes >10 seconds

**Solutions**:
- Use smaller models (3B instead of 7B)
- Simplify your query
- Check system resources (CPU/RAM)

### Wrong Model Selected

**Symptom**: Unexpected model chosen

**Solutions**:
- Use "Preferred Model" field to force selection
- Make query more specific
- Check routing reasoning in results

---

## 🚀 Quick Examples

### Example 1: Code Generation
```
Query: "Write a Python function to calculate fibonacci numbers"
Expected Model: phi3-local
Expected Response: Python code with explanation
```

### Example 2: General Question
```
Query: "What is machine learning?"
Expected Model: llama3.2-local
Expected Response: Clear explanation with examples
```

### Example 3: Creative Writing
```
Query: "Write a short story about a robot learning to paint"
Expected Model: llama3.2-local
Expected Response: Creative narrative
```

---

**Ready to try it?** Open http://localhost:3000 and start querying! 🎉

