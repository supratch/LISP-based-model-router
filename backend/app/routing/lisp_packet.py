#!/usr/bin/env python3
"""
LISP Packet Generator and Encapsulation
Implements LISP data plane packet encapsulation/decapsulation for AI workload routing.
"""

import struct
import socket
import hashlib
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
import ipaddress
import time
import json

import structlog

logger = structlog.get_logger(__name__)


class LISPPacketType(Enum):
    """LISP packet types."""
    DATA = 0  # Regular data packet
    CONTROL = 1  # Control plane packet


@dataclass
class LISPOuterHeader:
    """LISP outer header (UDP + LISP header)."""
    # UDP Header fields
    src_port: int = 4341  # LISP data port
    dst_port: int = 4341
    
    # LISP Header fields (8 bytes)
    flags: int = 0x08  # N=0, L=1, E=0, V=0, I=1 (Instance ID present)
    nonce: int = 0  # 24-bit nonce for echo-nonce
    instance_id: int = 0  # 24-bit instance ID for multi-tenancy
    lsb: int = 0  # Locator Status Bits (8 bits)
    
    def to_bytes(self) -> bytes:
        """Convert LISP header to bytes."""
        # LISP header format (RFC 6830):
        # Byte 0: Flags (N|L|E|V|I|flags)
        # Bytes 1-3: Nonce/Map-Version
        # Bytes 4-6: Instance ID / Locator Status Bits
        # Byte 7: Reserved
        
        header = bytearray(8)
        header[0] = self.flags
        
        # Pack nonce (24 bits)
        nonce_bytes = self.nonce.to_bytes(3, 'big')
        header[1:4] = nonce_bytes
        
        # Pack instance ID (24 bits)
        instance_bytes = self.instance_id.to_bytes(3, 'big')
        header[4:7] = instance_bytes
        
        # LSB in byte 7
        header[7] = self.lsb
        
        return bytes(header)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'LISPOuterHeader':
        """Parse LISP header from bytes."""
        if len(data) < 8:
            raise ValueError("LISP header must be at least 8 bytes")
        
        flags = data[0]
        nonce = int.from_bytes(data[1:4], 'big')
        instance_id = int.from_bytes(data[4:7], 'big')
        lsb = data[7]
        
        return cls(flags=flags, nonce=nonce, instance_id=instance_id, lsb=lsb)


@dataclass
class LISPPacket:
    """Complete LISP encapsulated packet."""
    # Outer IP header info
    outer_src_ip: str  # RLOC source
    outer_dst_ip: str  # RLOC destination
    
    # Inner IP header info
    inner_src_ip: str  # EID source
    inner_dst_ip: str  # EID destination
    
    # LISP header
    lisp_header: LISPOuterHeader = field(default_factory=LISPOuterHeader)
    
    # Payload
    payload: bytes = b""
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    packet_id: str = field(default="")
    workload_type: str = ""
    model_name: str = ""
    query_hash: str = ""
    
    def __post_init__(self):
        """Generate packet ID if not provided."""
        if not self.packet_id:
            self.packet_id = hashlib.md5(
                f"{self.outer_src_ip}{self.outer_dst_ip}{self.timestamp}".encode()
            ).hexdigest()[:12]
    
    def encapsulate(self) -> bytes:
        """Encapsulate inner packet with LISP header and outer IP."""
        # Build inner IP packet (simplified - just header + payload)
        inner_packet = self._build_inner_ip_packet()
        
        # Build LISP header
        lisp_header = self.lisp_header.to_bytes()
        
        # Build outer UDP header
        udp_header = self._build_udp_header(len(lisp_header) + len(inner_packet))
        
        # Build outer IP header
        outer_ip_header = self._build_outer_ip_header(len(udp_header) + len(lisp_header) + len(inner_packet))
        
        # Concatenate all parts
        full_packet = outer_ip_header + udp_header + lisp_header + inner_packet
        
        logger.info("LISP packet encapsulated",
                   packet_id=self.packet_id,
                   outer_src=self.outer_src_ip,
                   outer_dst=self.outer_dst_ip,
                   inner_src=self.inner_src_ip,
                   inner_dst=self.inner_dst_ip,
                   total_size=len(full_packet),
                   workload_type=self.workload_type)
        
        return full_packet
    
    def _build_inner_ip_packet(self) -> bytes:
        """Build simplified inner IP packet."""
        # Simplified IPv4 header (20 bytes) + payload
        src_ip = int(ipaddress.IPv4Address(self.inner_src_ip))
        dst_ip = int(ipaddress.IPv4Address(self.inner_dst_ip))
        
        # IPv4 header fields
        version_ihl = 0x45  # Version 4, IHL 5 (20 bytes)
        tos = 0
        total_length = 20 + len(self.payload)
        identification = 0x1234
        flags_fragment = 0
        ttl = 64
        protocol = 6  # TCP (simplified)
        checksum = 0  # Simplified - would calculate in production

        # Pack IPv4 header
        header = struct.pack('!BBHHHBBH4s4s',
                           version_ihl, tos, total_length,
                           identification, flags_fragment,
                           ttl, protocol, checksum,
                           src_ip.to_bytes(4, 'big'),
                           dst_ip.to_bytes(4, 'big'))

        return header + self.payload

    def _build_udp_header(self, payload_length: int) -> bytes:
        """Build UDP header for LISP encapsulation."""
        src_port = self.lisp_header.src_port
        dst_port = self.lisp_header.dst_port
        length = 8 + payload_length  # UDP header + payload
        checksum = 0  # Simplified

        return struct.pack('!HHHH', src_port, dst_port, length, checksum)

    def _build_outer_ip_header(self, payload_length: int) -> bytes:
        """Build outer IP header."""
        src_ip = int(ipaddress.IPv4Address(self.outer_src_ip))
        dst_ip = int(ipaddress.IPv4Address(self.outer_dst_ip))

        version_ihl = 0x45
        tos = 0
        total_length = 20 + payload_length
        identification = 0x5678
        flags_fragment = 0
        ttl = 64
        protocol = 17  # UDP
        checksum = 0

        return struct.pack('!BBHHHBBH4s4s',
                         version_ihl, tos, total_length,
                         identification, flags_fragment,
                         ttl, protocol, checksum,
                         src_ip.to_bytes(4, 'big'),
                         dst_ip.to_bytes(4, 'big'))

    @classmethod
    def decapsulate(cls, packet_data: bytes) -> 'LISPPacket':
        """Decapsulate LISP packet."""
        if len(packet_data) < 48:  # Min: outer IP(20) + UDP(8) + LISP(8) + inner IP(20)
            raise ValueError("Packet too short to be valid LISP packet")

        # Parse outer IP header
        outer_ip_header = packet_data[:20]
        outer_src_ip = str(ipaddress.IPv4Address(outer_ip_header[12:16]))
        outer_dst_ip = str(ipaddress.IPv4Address(outer_ip_header[16:20]))

        # Parse UDP header
        udp_header = packet_data[20:28]
        src_port, dst_port = struct.unpack('!HH', udp_header[:4])

        # Parse LISP header
        lisp_header_data = packet_data[28:36]
        lisp_header = LISPOuterHeader.from_bytes(lisp_header_data)
        lisp_header.src_port = src_port
        lisp_header.dst_port = dst_port

        # Parse inner IP header
        inner_ip_header = packet_data[36:56]
        inner_src_ip = str(ipaddress.IPv4Address(inner_ip_header[12:16]))
        inner_dst_ip = str(ipaddress.IPv4Address(inner_ip_header[16:20]))

        # Extract payload
        payload = packet_data[56:]

        return cls(
            outer_src_ip=outer_src_ip,
            outer_dst_ip=outer_dst_ip,
            inner_src_ip=inner_src_ip,
            inner_dst_ip=inner_dst_ip,
            lisp_header=lisp_header,
            payload=payload
        )

    def to_dict(self) -> Dict:
        """Convert packet to dictionary for JSON serialization."""
        return {
            "packet_id": self.packet_id,
            "timestamp": self.timestamp,
            "outer_header": {
                "src_ip": self.outer_src_ip,
                "dst_ip": self.outer_dst_ip,
                "src_port": self.lisp_header.src_port,
                "dst_port": self.lisp_header.dst_port
            },
            "lisp_header": {
                "flags": hex(self.lisp_header.flags),
                "nonce": self.lisp_header.nonce,
                "instance_id": self.lisp_header.instance_id,
                "lsb": self.lisp_header.lsb
            },
            "inner_header": {
                "src_ip": self.inner_src_ip,
                "dst_ip": self.inner_dst_ip
            },
            "metadata": {
                "workload_type": self.workload_type,
                "model_name": self.model_name,
                "query_hash": self.query_hash,
                "payload_size": len(self.payload)
            }
        }


class LISPPacketGenerator:
    """Generator for LISP packets post-routing."""

    def __init__(self):
        """Initialize packet generator."""
        self.packet_history: List[LISPPacket] = []
        self.stats = {
            "total_packets": 0,
            "total_bytes": 0,
            "packets_by_model": {}
        }
        logger.info("LISP packet generator initialized")

    def generate_packet(self,
                       source_eid: str,
                       dest_eid: str,
                       source_rloc: str,
                       dest_rloc: str,
                       payload: bytes,
                       workload_type: str = "",
                       model_name: str = "",
                       query_hash: str = "",
                       instance_id: int = 0) -> LISPPacket:
        """Generate a LISP encapsulated packet."""

        # Create LISP header with instance ID for multi-tenancy
        lisp_header = LISPOuterHeader(
            flags=0x08,  # Instance ID present
            nonce=self._generate_nonce(),
            instance_id=instance_id,
            lsb=0xFF  # All locators reachable
        )

        # Create LISP packet
        packet = LISPPacket(
            outer_src_ip=source_rloc,
            outer_dst_ip=dest_rloc,
            inner_src_ip=source_eid,
            inner_dst_ip=dest_eid,
            lisp_header=lisp_header,
            payload=payload,
            workload_type=workload_type,
            model_name=model_name,
            query_hash=query_hash
        )

        # Update statistics
        self.stats["total_packets"] += 1
        self.stats["total_bytes"] += len(payload)

        if model_name:
            if model_name not in self.stats["packets_by_model"]:
                self.stats["packets_by_model"][model_name] = 0
            self.stats["packets_by_model"][model_name] += 1

        # Store in history (keep last 100)
        self.packet_history.append(packet)
        if len(self.packet_history) > 100:
            self.packet_history.pop(0)

        logger.info("LISP packet generated",
                   packet_id=packet.packet_id,
                   model=model_name,
                   eid_src=source_eid,
                   rloc_dst=dest_rloc)

        return packet

    def _generate_nonce(self) -> int:
        """Generate 24-bit nonce for echo-nonce."""
        import random
        return random.randint(0, 0xFFFFFF)

    def generate_ai_query_packet(self,
                                source_eid: str,
                                routing_decision: Dict,
                                query: str,
                                query_hash: str) -> LISPPacket:
        """Generate LISP packet for AI query routing."""

        # Extract routing information
        model_name = routing_decision.get("selected_model", "unknown")
        dest_rloc = routing_decision.get("endpoint", "192.168.1.100")

        # Create payload with query metadata
        payload_data = {
            "query": query,
            "query_hash": query_hash,
            "model": model_name,
            "timestamp": time.time(),
            "routing_metadata": routing_decision.get("routing_metadata", {})
        }
        payload = json.dumps(payload_data).encode('utf-8')

        # Determine destination EID based on model (local models only)
        dest_eid_map = {
            "llama3.2-local": "10.1.0.100",
            "phi3-local": "10.1.0.101"
        }
        dest_eid = dest_eid_map.get(model_name, "10.1.0.1")

        # Use localhost for local models
        if "local" in model_name:
            dest_rloc = "127.0.0.1"

        # Generate packet
        return self.generate_packet(
            source_eid=source_eid,
            dest_eid=dest_eid,
            source_rloc="192.168.0.1",  # Client RLOC
            dest_rloc=dest_rloc,
            payload=payload,
            workload_type=routing_decision.get("routing_metadata", {}).get("query_analysis", {}).get("query_type", "general"),
            model_name=model_name,
            query_hash=query_hash,
            instance_id=1  # Default instance
        )

    def get_packet_stats(self) -> Dict:
        """Get packet generation statistics."""
        return {
            "total_packets": self.stats["total_packets"],
            "total_bytes": self.stats["total_bytes"],
            "packets_by_model": self.stats["packets_by_model"],
            "recent_packets": len(self.packet_history),
            "avg_packet_size": self.stats["total_bytes"] / max(1, self.stats["total_packets"])
        }

    def get_recent_packets(self, count: int = 10) -> List[Dict]:
        """Get recent packet information."""
        recent = self.packet_history[-count:] if len(self.packet_history) >= count else self.packet_history
        return [packet.to_dict() for packet in recent]

    def visualize_packet(self, packet: LISPPacket) -> str:
        """Generate ASCII visualization of LISP packet structure."""
        viz = []
        viz.append("=" * 70)
        viz.append("LISP ENCAPSULATED PACKET")
        viz.append("=" * 70)
        viz.append("")
        viz.append("┌─ OUTER IP HEADER ─────────────────────────────────────────────┐")
        viz.append(f"│ Source RLOC:      {packet.outer_src_ip:<45} │")
        viz.append(f"│ Destination RLOC: {packet.outer_dst_ip:<45} │")
        viz.append(f"│ Protocol:         UDP (17)                                     │")
        viz.append("└───────────────────────────────────────────────────────────────┘")
        viz.append("")
        viz.append("┌─ UDP HEADER ──────────────────────────────────────────────────┐")
        viz.append(f"│ Source Port:      {packet.lisp_header.src_port:<45} │")
        viz.append(f"│ Destination Port: {packet.lisp_header.dst_port:<45} │")
        viz.append("└───────────────────────────────────────────────────────────────┘")
        viz.append("")
        viz.append("┌─ LISP HEADER ─────────────────────────────────────────────────┐")
        viz.append(f"│ Flags:            {hex(packet.lisp_header.flags):<45} │")
        viz.append(f"│ Nonce:            {packet.lisp_header.nonce:<45} │")
        viz.append(f"│ Instance ID:      {packet.lisp_header.instance_id:<45} │")
        viz.append(f"│ LSB:              {hex(packet.lisp_header.lsb):<45} │")
        viz.append("└───────────────────────────────────────────────────────────────┘")
        viz.append("")
        viz.append("┌─ INNER IP HEADER ─────────────────────────────────────────────┐")
        viz.append(f"│ Source EID:       {packet.inner_src_ip:<45} │")
        viz.append(f"│ Destination EID:  {packet.inner_dst_ip:<45} │")
        viz.append("└───────────────────────────────────────────────────────────────┘")
        viz.append("")
        viz.append("┌─ PAYLOAD ─────────────────────────────────────────────────────┐")
        viz.append(f"│ Size:             {len(packet.payload)} bytes{' ' * (45 - len(str(len(packet.payload))) - 6)}│")
        viz.append(f"│ Workload Type:    {packet.workload_type:<45} │")
        viz.append(f"│ Model:            {packet.model_name:<45} │")
        viz.append(f"│ Query Hash:       {packet.query_hash:<45} │")
        viz.append("└───────────────────────────────────────────────────────────────┘")
        viz.append("")
        viz.append(f"Packet ID: {packet.packet_id}")
        viz.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packet.timestamp))}")
        viz.append("=" * 70)

        return "\n".join(viz)


# Global packet generator instance
_packet_generator = None


def get_packet_generator() -> LISPPacketGenerator:
    """Get global packet generator instance."""
    global _packet_generator
    if _packet_generator is None:
        _packet_generator = LISPPacketGenerator()
    return _packet_generator

