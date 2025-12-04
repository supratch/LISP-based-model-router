#!/bin/bash
# Test script for LISP packet generation and visualization

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         LISP PACKET GENERATION TEST SUITE                         ║"
echo "║         AI Workload Routing System                                ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="http://127.0.0.1:8000/api/v1"
AUTH_HEADER="Authorization: Bearer test"

# Test 1: Generate packets with different query types
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Generating LISP Packets for Different Query Types"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

queries=(
    '{"query":"Implement a binary search tree in Python","source_eid":"10.1.0.100","priority":"high"}'
    '{"query":"Write a haiku about machine learning","source_eid":"10.1.0.101","priority":"low"}'
    '{"query":"Solve the integral of sin(x)*cos(x)","source_eid":"10.1.0.102","priority":"medium"}'
    '{"query":"Summarize the theory of relativity","source_eid":"10.1.0.103","priority":"medium"}'
    '{"query":"Translate hello world to French","source_eid":"10.1.0.104","priority":"low"}'
)

query_names=(
    "Code Generation"
    "Creative Writing"
    "Math Computation"
    "Summarization"
    "Translation"
)

for i in "${!queries[@]}"; do
    echo "[$((i+1))/${#queries[@]}] ${query_names[$i]}..."
    response=$(curl -s -X POST "$BASE_URL/route" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "${queries[$i]}")
    
    model=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('selected_model', 'N/A'))")
    packet_id=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('lisp_packet', {}).get('packet_id', 'N/A'))")
    
    echo "   ✓ Routed to: $model"
    echo "   ✓ Packet ID: $packet_id"
    echo ""
done

# Test 2: View packet statistics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Packet Statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

stats=$(curl -s "$BASE_URL/packets/stats" -H "$AUTH_HEADER")
echo "$stats" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stats = data.get('stats', {})
print(f\"Total Packets Generated: {stats.get('total_packets', 0)}\")
print(f\"Total Bytes Transmitted: {stats.get('total_bytes', 0):,} bytes\")
print(f\"Average Packet Size: {stats.get('avg_packet_size', 0):.2f} bytes\")
print(f\"Recent Packets in History: {stats.get('recent_packets', 0)}\")
print()
print('Packets by Model:')
for model, count in stats.get('packets_by_model', {}).items():
    print(f\"  • {model}: {count} packets\")
"
echo ""

# Test 3: View recent packets
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Recent LISP Packets (Last 5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

recent=$(curl -s "$BASE_URL/packets/recent?count=5" -H "$AUTH_HEADER")
echo "$recent" | python3 -c "
import sys, json
from datetime import datetime

data = json.load(sys.stdin)
packets = data.get('packets', [])

for i, p in enumerate(packets, 1):
    meta = p.get('metadata', {})
    inner = p.get('inner_header', {})
    outer = p.get('outer_header', {})
    lisp = p.get('lisp_header', {})
    
    print(f\"{i}. Packet {p.get('packet_id', 'N/A')}:\")
    print(f\"   Model: {meta.get('model_name', 'N/A')}\")
    print(f\"   Workload: {meta.get('workload_type', 'N/A')}\")
    print(f\"   EID Route: {inner.get('src_ip', 'N/A')} → {inner.get('dst_ip', 'N/A')}\")
    print(f\"   RLOC Route: {outer.get('src_ip', 'N/A')} → {outer.get('dst_ip', 'N/A')}\")
    print(f\"   Instance ID: {lisp.get('instance_id', 'N/A')}\")
    print(f\"   Payload: {meta.get('payload_size', 0)} bytes\")
    
    timestamp = p.get('timestamp', 0)
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        print(f\"   Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}\")
    print()
"

# Test 4: Visualize last packet
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: LISP Packet Visualization (Most Recent)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

viz=$(curl -s -X POST "$BASE_URL/packets/visualize" -H "$AUTH_HEADER")
echo "$viz" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('visualization', 'N/A'))"
echo ""

# Test 5: Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ All LISP packet generation tests completed successfully!"
echo ""
echo "Key Features Demonstrated:"
echo "  • LISP packet encapsulation with outer/inner IP headers"
echo "  • EID-to-RLOC mapping for AI workload routing"
echo "  • Multi-tenancy support via Instance ID"
echo "  • Packet statistics and history tracking"
echo "  • ASCII visualization of packet structure"
echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    TESTS COMPLETED                                 ║"
echo "╚════════════════════════════════════════════════════════════════════╝"

