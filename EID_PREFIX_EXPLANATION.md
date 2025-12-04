# 🔍 "No Matching EID Prefix Found" - Explanation

## What Does This Mean?

The error **"No matching EID prefix found"** occurs when the LISP router cannot find a valid EID (Endpoint Identifier) prefix that matches the source EID you provided in your query.

---

## 🧠 Understanding EID Prefixes

### What is an EID Prefix?

An **EID Prefix** is a network address range that identifies a group of endpoints in the LISP routing system. Think of it like a postal code range - it groups similar addresses together.

### Configured EID Prefixes

The system has **three pre-configured EID prefix ranges**:

| EID Prefix | Purpose | Routed Models |
|------------|---------|---------------|
| `10.1.0.0/16` | General AI workloads | llama3.2-local, phi3-local |
| `10.2.0.0/16` | Code generation workloads | phi3-local |
| `10.3.0.0/16` | Creative/general workloads | llama3.2-local |

### What Does `/16` Mean?

- `/16` means the first **16 bits** of the IP address are fixed
- For `10.1.0.0/16`, this includes all addresses from `10.1.0.0` to `10.1.255.255`
- That's **65,536 possible addresses** in each range!

---

## 🔍 How EID Matching Works

### Step-by-Step Process

1. **User provides Source EID** (e.g., `10.1.0.50`)
2. **Router checks all configured prefixes**:
   - Is `10.1.0.50` in `10.1.0.0/16`? ✅ YES
   - Is `10.1.0.50` in `10.2.0.0/16`? ❌ NO
   - Is `10.1.0.50` in `10.3.0.0/16`? ❌ NO
3. **Best match selected**: `10.1.0.0/16`
4. **Models retrieved**: llama3.2-local, phi3-local

### Code Location

<augment_code_snippet path="backend/app/routing/lisp_router.py" mode="EXCERPT">
````python
def _find_matching_eid_prefix(self, eid: str) -> Optional[str]:
    """Find the most specific matching EID prefix."""
    try:
        eid_addr = ipaddress.ip_address(eid)
        best_match = None
        best_prefix_len = -1
        
        for prefix_str in self.map_cache.keys():
            try:
                prefix = ipaddress.ip_network(prefix_str)
                if eid_addr in prefix and prefix.prefixlen > best_prefix_len:
                    best_match = prefix_str
                    best_prefix_len = prefix.prefixlen
````
</augment_code_snippet>

---

## ❌ When Does "No Matching EID Prefix Found" Occur?

### Common Scenarios

#### 1. **Invalid Source EID**

**Example**: Source EID = `192.168.1.100`

**Problem**: This address is NOT in any configured prefix:
- ❌ Not in `10.1.0.0/16` (10.1.x.x)
- ❌ Not in `10.2.0.0/16` (10.2.x.x)
- ❌ Not in `10.3.0.0/16` (10.3.x.x)

**Result**: "No matching EID prefix found"

#### 2. **Typo in Source EID**

**Example**: Source EID = `10.4.0.1` (should be `10.1.0.1`)

**Problem**: `10.4.x.x` range is not configured

**Result**: "No matching EID prefix found"

#### 3. **Empty or Malformed EID**

**Example**: Source EID = `""` or `invalid-ip`

**Problem**: Cannot parse as valid IP address

**Result**: Error or "No matching EID prefix found"

---

## ✅ Valid Source EID Examples

### Examples That WILL Work

| Source EID | Matches Prefix | Routed To |
|------------|----------------|-----------|
| `10.1.0.1` | `10.1.0.0/16` | llama3.2-local, phi3-local |
| `10.1.0.50` | `10.1.0.0/16` | llama3.2-local, phi3-local |
| `10.1.255.255` | `10.1.0.0/16` | llama3.2-local, phi3-local |
| `10.2.0.1` | `10.2.0.0/16` | phi3-local |
| `10.2.100.50` | `10.2.0.0/16` | phi3-local |
| `10.3.0.1` | `10.3.0.0/16` | llama3.2-local |
| `10.3.50.100` | `10.3.0.0/16` | llama3.2-local |

### Examples That WILL NOT Work

| Source EID | Why It Fails |
|------------|--------------|
| `192.168.1.1` | Not in 10.x.x.x range |
| `10.0.0.1` | Not in configured prefixes (10.0 ≠ 10.1/10.2/10.3) |
| `10.4.0.1` | 10.4 prefix not configured |
| `172.16.0.1` | Completely different range |
| `localhost` | Not a valid IP address |
| `10.1` | Incomplete IP address |

---

## 🔧 How to Fix This Error

### Solution 1: Use a Valid Source EID

**In the Query Interface**, use one of these default values:

```
✅ 10.1.0.1    (General workloads)
✅ 10.2.0.1    (Code generation)
✅ 10.3.0.1    (Creative workloads)
```

### Solution 2: Check Your Input

1. Open the Query Routing Interface
2. Look at the **"Source EID"** field
3. Make sure it's in the format: `10.X.Y.Z` where X is 1, 2, or 3

### Solution 3: Add New EID Prefixes (Advanced)

If you need to support different EID ranges, edit the configuration:

<augment_code_snippet path="backend/app/routing/lisp_router.py" mode="EXCERPT">
````python
# Add to map_cache in _populate_initial_map_cache()
self.map_cache["10.4.0.0/16"] = MapCacheEntry(
    eid_prefix=EIDPrefix("10.4.0.0", 16, 1),
    rlocs=your_rlocs,
    ttl=3600,
    authoritative=True,
    created_at=time.time()
)
````
</augment_code_snippet>

---

## 📊 Visual Explanation

### EID Prefix Ranges

```
┌─────────────────────────────────────────────────────┐
│ Configured EID Prefixes (Map Cache)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  10.1.0.0/16  ┌──────────────────────────────┐    │
│               │ 10.1.0.0 → 10.1.255.255      │    │
│               │ Models: llama3.2, phi3       │    │
│               └──────────────────────────────┘    │
│                                                     │
│  10.2.0.0/16  ┌──────────────────────────────┐    │
│               │ 10.2.0.0 → 10.2.255.255      │    │
│               │ Models: phi3                 │    │
│               └──────────────────────────────┘    │
│                                                     │
│  10.3.0.0/16  ┌──────────────────────────────┐    │
│               │ 10.3.0.0 → 10.3.255.255      │    │
│               │ Models: llama3.2             │    │
│               └──────────────────────────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘

Your Source EID: 10.1.0.50
                 ↓
         Matches: 10.1.0.0/16 ✅
                 ↓
         Routes to: llama3.2-local or phi3-local
```

### What Happens with Invalid EID

```
Your Source EID: 192.168.1.100
                 ↓
         Check: 10.1.0.0/16? ❌ NO
         Check: 10.2.0.0/16? ❌ NO
         Check: 10.3.0.0/16? ❌ NO
                 ↓
         Result: "No matching EID prefix found" ⚠️
```

---

## 🎯 Quick Reference

### Default Source EIDs to Use

| Use Case | Source EID | Why |
|----------|------------|-----|
| General queries | `10.1.0.1` | Access to all models |
| Code generation | `10.2.0.1` | Optimized for Phi-3 |
| Creative writing | `10.3.0.1` | Optimized for Llama 3.2 |

### Troubleshooting Checklist

- [ ] Is your Source EID in the format `10.X.Y.Z`?
- [ ] Is X equal to 1, 2, or 3?
- [ ] Are Y and Z between 0 and 255?
- [ ] Did you type the IP address correctly?
- [ ] Is the backend running and initialized?

---

## 💡 Why This Design?

### Benefits of EID Prefixes

1. **Logical Grouping**: Group similar workloads together
2. **Scalability**: Support thousands of endpoints per prefix
3. **Flexibility**: Easy to add new prefixes for new workload types
4. **Performance**: Fast prefix matching using IP address libraries
5. **Mobility**: Endpoints can move without changing their EID

---

**Need Help?** Check the Query Interface default value or use `10.1.0.1` as a safe default!

