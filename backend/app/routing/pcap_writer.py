#!/usr/bin/env python3
"""
PCAP Writer for LISP Packets
Generates PCAP files from LISP packets for analysis in Wireshark and other tools.
"""

import struct
import time
from typing import List, BinaryIO
from io import BytesIO

import structlog

logger = structlog.get_logger(__name__)


class PCAPWriter:
    """Writer for PCAP (Packet Capture) files."""
    
    # PCAP Global Header constants
    PCAP_MAGIC_NUMBER = 0xa1b2c3d4
    PCAP_VERSION_MAJOR = 2
    PCAP_VERSION_MINOR = 4
    PCAP_THISZONE = 0
    PCAP_SIGFIGS = 0
    PCAP_SNAPLEN = 65535
    PCAP_NETWORK = 1  # Ethernet
    
    def __init__(self):
        """Initialize PCAP writer."""
        self.packets_written = 0
        logger.info("PCAP writer initialized")
    
    def write_global_header(self, output: BinaryIO):
        """Write PCAP global header."""
        header = struct.pack(
            '<IHHIIII',
            self.PCAP_MAGIC_NUMBER,
            self.PCAP_VERSION_MAJOR,
            self.PCAP_VERSION_MINOR,
            self.PCAP_THISZONE,
            self.PCAP_SIGFIGS,
            self.PCAP_SNAPLEN,
            self.PCAP_NETWORK
        )
        output.write(header)
        logger.debug("PCAP global header written")
    
    def write_packet_header(self, output: BinaryIO, packet_data: bytes, timestamp: float):
        """Write PCAP packet header."""
        ts_sec = int(timestamp)
        ts_usec = int((timestamp - ts_sec) * 1000000)
        incl_len = len(packet_data)
        orig_len = len(packet_data)
        
        header = struct.pack(
            '<IIII',
            ts_sec,
            ts_usec,
            incl_len,
            orig_len
        )
        output.write(header)
    
    def write_ethernet_frame(self, output: BinaryIO, ip_packet: bytes):
        """Write Ethernet frame wrapper around IP packet."""
        # Ethernet header (14 bytes)
        dst_mac = b'\x00\x00\x00\x00\x00\x01'  # Destination MAC
        src_mac = b'\x00\x00\x00\x00\x00\x02'  # Source MAC
        ethertype = b'\x08\x00'  # IPv4
        
        ethernet_frame = dst_mac + src_mac + ethertype + ip_packet
        return ethernet_frame
    
    def write_lisp_packet(self, output: BinaryIO, lisp_packet, include_ethernet: bool = True):
        """Write a single LISP packet to PCAP file."""
        from app.routing.lisp_packet import LISPPacket
        
        if not isinstance(lisp_packet, LISPPacket):
            raise ValueError("Expected LISPPacket instance")
        
        # Encapsulate the packet to get the full binary data
        packet_data = lisp_packet.encapsulate()
        
        # Wrap in Ethernet frame if requested
        if include_ethernet:
            packet_data = self.write_ethernet_frame(output, packet_data)
        
        # Write packet header and data
        self.write_packet_header(output, packet_data, lisp_packet.timestamp)
        output.write(packet_data)
        
        self.packets_written += 1
        logger.debug("LISP packet written to PCAP",
                    packet_id=lisp_packet.packet_id,
                    size=len(packet_data))
    
    def create_pcap_from_packets(self, packets: List, filename: str = None) -> bytes:
        """Create PCAP file from list of LISP packets."""
        output = BytesIO()
        
        # Write global header
        self.write_global_header(output)
        
        # Write all packets
        for packet in packets:
            try:
                self.write_lisp_packet(output, packet)
            except Exception as e:
                logger.error("Error writing packet to PCAP",
                           packet_id=getattr(packet, 'packet_id', 'unknown'),
                           error=str(e))
                continue
        
        pcap_data = output.getvalue()
        output.close()
        
        logger.info("PCAP file created",
                   packets=self.packets_written,
                   size=len(pcap_data),
                   filename=filename or "memory")
        
        return pcap_data
    
    def save_pcap_file(self, packets: List, filename: str):
        """Save PCAP file to disk."""
        pcap_data = self.create_pcap_from_packets(packets, filename)
        
        with open(filename, 'wb') as f:
            f.write(pcap_data)
        
        logger.info("PCAP file saved to disk",
                   filename=filename,
                   size=len(pcap_data),
                   packets=self.packets_written)
        
        return filename


def create_pcap_from_packet_dicts(packet_dicts: List[dict]) -> bytes:
    """Create PCAP from packet dictionaries (for API responses)."""
    from app.routing.lisp_packet import LISPPacket, LISPOuterHeader
    
    # Convert dictionaries back to LISPPacket objects
    packets = []
    for pdict in packet_dicts:
        try:
            # Reconstruct LISP header
            lisp_header_data = pdict.get('lisp_header', {})
            lisp_header = LISPOuterHeader(
                src_port=pdict.get('outer_header', {}).get('src_port', 4341),
                dst_port=pdict.get('outer_header', {}).get('dst_port', 4341),
                flags=int(lisp_header_data.get('flags', '0x8'), 16),
                nonce=lisp_header_data.get('nonce', 0),
                instance_id=lisp_header_data.get('instance_id', 0),
                lsb=lisp_header_data.get('lsb', 0xFF)
            )
            
            # Reconstruct packet
            packet = LISPPacket(
                outer_src_ip=pdict.get('outer_header', {}).get('src_ip', '192.168.0.1'),
                outer_dst_ip=pdict.get('outer_header', {}).get('dst_ip', '192.168.1.100'),
                inner_src_ip=pdict.get('inner_header', {}).get('src_ip', '10.1.0.1'),
                inner_dst_ip=pdict.get('inner_header', {}).get('dst_ip', '10.1.0.100'),
                lisp_header=lisp_header,
                payload=b"",  # Payload not stored in dict
                timestamp=pdict.get('timestamp', time.time()),
                packet_id=pdict.get('packet_id', ''),
                workload_type=pdict.get('metadata', {}).get('workload_type', ''),
                model_name=pdict.get('metadata', {}).get('model_name', ''),
                query_hash=pdict.get('metadata', {}).get('query_hash', '')
            )
            packets.append(packet)
        except Exception as e:
            logger.error("Error reconstructing packet", error=str(e))
            continue
    
    # Create PCAP
    writer = PCAPWriter()
    return writer.create_pcap_from_packets(packets)

