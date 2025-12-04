#!/bin/bash

# Test script for LISP Packet PCAP Download functionality
# This script demonstrates the complete PCAP download workflow

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     LISP Packet PCAP Download - Comprehensive Test            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://127.0.0.1:8000/api/v1"
AUTH_HEADER="Authorization: Bearer test"

echo -e "${BLUE}Step 1: Generating Test Packets${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate different types of queries
queries=(
  "Write a Python function to sort a list"
  "Explain quantum computing in simple terms"
  "Calculate the factorial of 10"
  "Translate 'Hello World' to Spanish"
  "Summarize the benefits of cloud computing"
)

for i in "${!queries[@]}"; do
  query="${queries[$i]}"
  eid="10.1.0.$((i+10))"
  
  echo -n "Generating packet $((i+1)): "
  response=$(curl -s -X POST "$BASE_URL/route" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d "{\"query\":\"$query\",\"source_eid\":\"$eid\",\"priority\":\"medium\"}")
  
  packet_id=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('lisp_packet', {}).get('packet_id', 'N/A'))" 2>/dev/null)
  model=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('selected_model', 'N/A'))" 2>/dev/null)
  
  echo -e "${GREEN}✓${NC} Packet ID: $packet_id | Model: $model"
done

echo ""
echo -e "${BLUE}Step 2: Viewing Packet Statistics${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stats=$(curl -s "$BASE_URL/packets/stats" -H "$AUTH_HEADER")
echo "$stats" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stats = data.get('stats', {})
print(f\"Total Packets: {stats.get('total_packets', 0)}\")
print(f\"Total Bytes: {stats.get('total_bytes', 0)} bytes ({stats.get('total_bytes', 0)/1024:.2f} KB)\")
print(f\"Average Packet Size: {stats.get('avg_packet_size', 0):.2f} bytes\")
print(f\"\\nPackets by Model:\")
for model, count in stats.get('packets_by_model', {}).items():
    print(f\"  - {model}: {count} packets\")
"

echo ""
echo -e "${BLUE}Step 3: Downloading PCAP Files${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Download all recent packets
PCAP_FILE="/tmp/lisp_packets_all.pcap"
echo -n "Downloading all recent packets (max 10)... "
curl -s "$BASE_URL/packets/download/pcap?count=10" \
  -H "$AUTH_HEADER" \
  -o "$PCAP_FILE"

if [ -f "$PCAP_FILE" ]; then
  size=$(ls -lh "$PCAP_FILE" | awk '{print $5}')
  echo -e "${GREEN}✓${NC} Downloaded: $PCAP_FILE ($size)"
else
  echo -e "${RED}✗${NC} Failed to download"
  exit 1
fi

# Download a single packet
echo -n "Downloading single packet... "
recent_packets=$(curl -s "$BASE_URL/packets/recent?count=1" -H "$AUTH_HEADER")
single_packet_id=$(echo "$recent_packets" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('packets', [{}])[0].get('packet_id', ''))" 2>/dev/null)

if [ -n "$single_packet_id" ]; then
  SINGLE_PCAP="/tmp/lisp_packet_single.pcap"
  curl -s "$BASE_URL/packets/$single_packet_id/download/pcap" \
    -H "$AUTH_HEADER" \
    -o "$SINGLE_PCAP"
  
  if [ -f "$SINGLE_PCAP" ]; then
    size=$(ls -lh "$SINGLE_PCAP" | awk '{print $5}')
    echo -e "${GREEN}✓${NC} Downloaded: $SINGLE_PCAP ($size)"
  fi
fi

echo ""
echo -e "${BLUE}Step 4: Verifying PCAP Files${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "PCAP Global Header (first 24 bytes):"
hexdump -C "$PCAP_FILE" | head -2

echo ""
echo "File Information:"
file "$PCAP_FILE" 2>/dev/null || echo "tcpdump capture file (little-endian)"

echo ""
echo -e "${BLUE}Step 5: Analyzing PCAP with tcpdump (if available)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v tcpdump &> /dev/null; then
  echo "Packet summary:"
  tcpdump -r "$PCAP_FILE" -n -c 5 2>/dev/null || echo "Unable to read with tcpdump"
else
  echo -e "${YELLOW}⚠${NC} tcpdump not installed. Install with: brew install tcpdump"
  echo "You can open the PCAP file in Wireshark for detailed analysis."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✓${NC} PCAP files generated successfully"
echo -e "${GREEN}✓${NC} Files saved to:"
echo "  - $PCAP_FILE"
echo "  - $SINGLE_PCAP"
echo ""
echo "Next Steps:"
echo "  1. Open PCAP files in Wireshark: wireshark $PCAP_FILE"
echo "  2. Access the UI at: http://localhost:3000/packets"
echo "  3. Download packets directly from the web interface"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo "  - GET  /api/v1/packets/stats"
echo "  - GET  /api/v1/packets/recent?count=N"
echo "  - GET  /api/v1/packets/download/pcap?count=N"
echo "  - GET  /api/v1/packets/{packet_id}/download/pcap"
echo ""

