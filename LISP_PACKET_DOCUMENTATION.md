# LISP Packet Generation Documentation

## Overview

The AI Workload Routing System now includes comprehensive LISP (Locator/Identifier Separation Protocol) packet generation and encapsulation capabilities. This feature generates actual LISP-encapsulated packets post-routing, providing a complete implementation of the LISP data plane for AI workload distribution.

## Architecture

### LISP Packet Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    OUTER IP HEADER                          │
│  - Source RLOC (Routing Locator)                           │
│  - Destination RLOC                                        │
│  - Protocol: UDP (17)                                      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    UDP HEADER                               │
│  - Source Port: 4341 (LISP data port)                     │
│  - Destination Port: 4341                                  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    LISP HEADER (8 bytes)                    │
│  - Flags: 0x08 (Instance ID present)                       │
│  - Nonce: 24-bit random value                             │
│  - Instance ID: 24-bit tenant identifier                   │
│  - LSB: Locator Status Bits (8 bits)                      │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    INNER IP HEADER                          │
│  - Source EID (Endpoint Identifier)                        │
│  - Destination EID                                         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    PAYLOAD                                  │
│  - Query data                                              │
│  - Routing metadata                                        │
│  - Model information                                       │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. LISPOuterHeader
Represents the 8-byte LISP header as defined in RFC 6830:
- **Flags**: Control bits (N, L, E, V, I flags)
- **Nonce**: 24-bit echo-nonce for path validation
- **Instance ID**: 24-bit identifier for multi-tenancy support
- **LSB**: Locator Status Bits indicating RLOC reachability

### 2. LISPPacket
Complete LISP encapsulated packet containing:
- Outer IP header (RLOC addressing)
- UDP header (port 4341)
- LISP header
- Inner IP header (EID addressing)
- Payload (query data + metadata)

### 3. LISPPacketGenerator
Manages packet generation and tracking:
- Generates LISP packets post-routing
- Maintains packet history (last 100 packets)
- Tracks statistics (total packets, bytes, per-model counts)
- Provides visualization capabilities

## API Endpoints

### POST /api/v1/route
Routes a query and generates a LISP packet.

**Request:**
```json
{
  "query": "Write a Python function to calculate factorial",
  "source_eid": "10.1.0.5",
  "priority": "medium"
}
```

**Response includes:**
```json
{
  "selected_model": "phi3-local",
  "endpoint": "127.0.0.1",
  "lisp_packet": {
    "packet_id": "2dc564948e89",
    "timestamp": 1764082056.39452,
    "outer_header": {
      "src_ip": "192.168.0.1",
      "dst_ip": "127.0.0.1",
      "src_port": 4341,
      "dst_port": 4341
    },
    "lisp_header": {
      "flags": "0x8",
      "nonce": 7748299,
      "instance_id": 1,
      "lsb": 255
    },
    "inner_header": {
      "src_ip": "10.1.0.5",
      "dst_ip": "10.4.0.101"
    },
    "metadata": {
      "workload_type": "code_generation",
      "model_name": "phi3-local",
      "query_hash": "813a6050",
      "payload_size": 493
    }
  }
}
```

### GET /api/v1/packets/stats
Get packet generation statistics.

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_packets": 11,
    "total_bytes": 5363,
    "packets_by_model": {
      "claude-3": 5,
      "phi3-local": 6
    },
    "recent_packets": 11,
    "avg_packet_size": 487.55
  }
}
```

### GET /api/v1/packets/recent?count=10
Get recent LISP packets.

### GET /api/v1/packets/{packet_id}
Get detailed information about a specific packet.

### POST /api/v1/packets/visualize
Visualize the most recent LISP packet with ASCII art.

## EID-to-RLOC Mapping

### Model-Specific EID Assignments
- **GPT-4**: 10.1.0.100 → RLOC 192.168.1.100
- **Claude-3**: 10.1.0.200 → RLOC 192.168.2.100
- **Llama 3.2 Local**: 10.4.0.100 → RLOC 127.0.0.1
- **Phi-3 Local**: 10.4.0.101 → RLOC 127.0.0.1

### EID Prefix Ranges
- **10.1.0.0/16**: General AI workloads (GPT-4, Claude-3)
- **10.2.0.0/16**: Fast response workloads
- **10.3.0.0/16**: Complex reasoning workloads
- **10.4.0.0/16**: Local model workloads

## Usage Examples

### Generate and View a Packet
```bash
# Route a query and generate packet
curl -X POST "http://127.0.0.1:8000/api/v1/route" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{"query":"Write a sorting algorithm","source_eid":"10.1.0.10"}'

# Visualize the packet
curl -X POST "http://127.0.0.1:8000/api/v1/packets/visualize" \
  -H "Authorization: Bearer test"
```

### Download PCAP Files

#### Download Recent Packets
```bash
# Download last 10 packets as PCAP
curl "http://127.0.0.1:8000/api/v1/packets/download/pcap?count=10" \
  -H "Authorization: Bearer test" \
  -o lisp_packets.pcap

# Open in Wireshark
wireshark lisp_packets.pcap
```

#### Download Single Packet
```bash
# Get packet ID from recent packets
PACKET_ID=$(curl -s "http://127.0.0.1:8000/api/v1/packets/recent?count=1" \
  -H "Authorization: Bearer test" | jq -r '.packets[0].packet_id')

# Download specific packet
curl "http://127.0.0.1:8000/api/v1/packets/${PACKET_ID}/download/pcap" \
  -H "Authorization: Bearer test" \
  -o packet_${PACKET_ID}.pcap
```

#### Analyze with tcpdump
```bash
# View packet summary
tcpdump -r lisp_packets.pcap -n

# Detailed packet inspection
tcpdump -r lisp_packets.pcap -n -vv -X
```

## Web Interface

The system includes a comprehensive web interface for packet management:

### Accessing the Packet Viewer
1. Navigate to `http://localhost:3000/packets`
2. View real-time packet statistics
3. Browse recent LISP packets
4. Download PCAP files with one click
5. Visualize packet structure

### Features
- **Real-time Statistics**: Total packets, bytes transferred, packets by model
- **Packet Browser**: View all recent packets with filtering
- **One-Click Download**: Download individual or bulk PCAP files
- **Packet Visualization**: ASCII art representation of packet structure
- **Auto-refresh**: Statistics update every 5 seconds

## PCAP File Format

The generated PCAP files follow the standard libpcap format:

### File Structure
```
[PCAP Global Header - 24 bytes]
  - Magic Number: 0xa1b2c3d4 (little-endian)
  - Version: 2.4
  - Timezone: 0
  - Timestamp accuracy: 0
  - Snapshot length: 65535
  - Link-layer type: 1 (Ethernet)

[Packet 1]
  [Packet Header - 16 bytes]
    - Timestamp (seconds)
    - Timestamp (microseconds)
    - Captured length
    - Original length
  [Packet Data]
    [Ethernet Frame - 14 bytes]
    [IP Header - 20 bytes (Outer/RLOC)]
    [UDP Header - 8 bytes]
    [LISP Header - 8 bytes]
    [IP Header - 20 bytes (Inner/EID)]
    [Payload]

[Packet 2]
...
```

## Wireshark Analysis

### Display Filters
```
# Show only LISP packets (UDP port 4341)
udp.port == 4341

# Filter by source RLOC
ip.src == 192.168.0.1

# Filter by destination EID (requires decapsulation)
# Note: Wireshark may not automatically decode LISP encapsulation
```

### Decoding LISP Packets
1. Open PCAP in Wireshark
2. Right-click on a packet → Decode As
3. Select "UDP port 4341" → "LISP Data"
4. View decapsulated inner IP headers

## Integration Examples

### Python
```python
import requests

# Download PCAP
response = requests.get(
    'http://127.0.0.1:8000/api/v1/packets/download/pcap?count=10',
    headers={'Authorization': 'Bearer test'}
)

with open('packets.pcap', 'wb') as f:
    f.write(response.content)

# Analyze with scapy
from scapy.all import rdpcap
packets = rdpcap('packets.pcap')
for pkt in packets:
    print(pkt.summary())
```

### JavaScript/TypeScript
```typescript
// Download PCAP from browser
async function downloadPCAP(count: number) {
  const response = await fetch(
    `http://127.0.0.1:8000/api/v1/packets/download/pcap?count=${count}`,
    { headers: { 'Authorization': 'Bearer test' } }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'lisp_packets.pcap';
  a.click();
}
```

## Troubleshooting

### PCAP File Won't Open
- Verify magic number: `hexdump -C file.pcap | head -1`
- Should start with: `d4 c3 b2 a1` (little-endian)
- Check file size: `ls -lh file.pcap`

### No Packets in PCAP
- Ensure packets have been generated: `curl http://127.0.0.1:8000/api/v1/packets/stats`
- Check packet history is not empty
- Verify API endpoint is accessible

### Wireshark Shows Malformed Packets
- LISP encapsulation may not be automatically decoded
- Use "Decode As" feature to specify LISP protocol
- Inner IP headers are encapsulated and may need manual inspection

## Performance Considerations

- PCAP files are generated in-memory for fast downloads
- Maximum 100 packets per download (configurable)
- Packet history limited to last 100 packets
- Average PCAP file size: ~500 bytes per packet
- Download time: < 1 second for 100 packets

