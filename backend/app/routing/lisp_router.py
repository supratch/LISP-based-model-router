#!/usr/bin/env python3
"""
LISP (Locator/Identifier Separation Protocol) Router
Implements LISP-based routing for AI workload distribution.
"""

import asyncio
import json
import socket
import struct
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ipaddress
import time

import structlog

logger = structlog.get_logger(__name__)


class LISPMessageType(Enum):
    """LISP message types for control plane communication."""
    MAP_REQUEST = 1
    MAP_REPLY = 2
    MAP_REGISTER = 3
    MAP_NOTIFY = 4
    ENCAPSULATED_CONTROL_MESSAGE = 8


@dataclass
class EIDPrefix:
    """Endpoint Identifier (EID) prefix definition."""
    prefix: str
    prefix_length: int
    afi: int  # Address Family Identifier
    
    def __post_init__(self):
        """Validate EID prefix format."""
        try:
            if self.afi == 1:  # IPv4
                ipaddress.IPv4Network(f"{self.prefix}/{self.prefix_length}")
            elif self.afi == 2:  # IPv6
                ipaddress.IPv6Network(f"{self.prefix}/{self.prefix_length}")
        except ValueError as e:
            raise ValueError(f"Invalid EID prefix: {e}")


@dataclass
class RLOCMapping:
    """Routing Locator (RLOC) mapping information."""
    rloc: str
    priority: int
    weight: int
    multicast_priority: int
    multicast_weight: int
    local_locator: bool
    reachable: bool
    load_factor: float = 0.0
    last_updated: float = 0.0
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.last_updated == 0.0:
            self.last_updated = time.time()


@dataclass
class MapCacheEntry:
    """Map cache entry for EID-to-RLOC mappings."""
    eid_prefix: EIDPrefix
    rlocs: List[RLOCMapping]
    ttl: int
    authoritative: bool
    created_at: float
    access_count: int = 0
    
    def __post_init__(self):
        """Initialize creation timestamp if not provided."""
        if not hasattr(self, 'created_at') or self.created_at == 0.0:
            self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if the map cache entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    def get_best_rloc(self) -> Optional[RLOCMapping]:
        """Get the best RLOC based on priority, weight, and load."""
        reachable_rlocs = [rloc for rloc in self.rlocs if rloc.reachable]
        
        if not reachable_rlocs:
            return None
        
        # Sort by priority (lower is better), then by load factor
        reachable_rlocs.sort(key=lambda r: (r.priority, r.load_factor))
        
        # Implement weighted selection among same priority RLOCs
        min_priority = reachable_rlocs[0].priority
        same_priority_rlocs = [r for r in reachable_rlocs if r.priority == min_priority]
        
        if len(same_priority_rlocs) == 1:
            return same_priority_rlocs[0]
        
        # Weighted random selection based on weight and inverse load factor
        total_weight = sum(max(1, r.weight * (1 - r.load_factor)) for r in same_priority_rlocs)
        
        if total_weight > 0:
            import random
            rand_val = random.uniform(0, total_weight)
            current_weight = 0
            
            for rloc in same_priority_rlocs:
                current_weight += max(1, rloc.weight * (1 - rloc.load_factor))
                if rand_val <= current_weight:
                    return rloc
        
        return same_priority_rlocs[0]


class LISPRouter:
    """LISP router implementation for AI workload distribution."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize LISP router with configuration."""
        self.config = config or {}
        self.map_cache: Dict[str, MapCacheEntry] = {}
        self.eid_mappings: Dict[str, List[str]] = {}  # EID to AI model mappings
        self.running = False
        self.control_socket: Optional[socket.socket] = None
        
        # Default AI model EID assignments
        self._initialize_ai_model_mappings()
        
        logger.info("LISP router initialized", config=self.config)
    
    def _initialize_ai_model_mappings(self):
        """Initialize EID-to-AI-model mappings."""
        # Map EID prefixes to AI model types (local models only)
        self.eid_mappings = {
            "10.1.0.0/16": ["llama3.2-local", "phi3-local"],  # General AI workloads
            "10.2.0.0/16": ["phi3-local"],                     # Code generation workloads
            "10.3.0.0/16": ["llama3.2-local"],                 # Creative/general workloads
        }

        # Initialize map cache with AI model RLOCs
        self._populate_initial_map_cache()

    def _populate_initial_map_cache(self):
        """Populate initial map cache with AI model locations."""
        # Llama 3.2 Local - localhost deployment
        llama_rlocs = [
            RLOCMapping(
                rloc="127.0.0.1",
                priority=10,
                weight=100,
                multicast_priority=10,
                multicast_weight=100,
                local_locator=True,
                reachable=True,
                load_factor=0.3
            )
        ]

        # Phi-3 Local - localhost deployment
        phi3_rlocs = [
            RLOCMapping(
                rloc="127.0.0.1",
                priority=10,
                weight=100,
                multicast_priority=10,
                multicast_weight=100,
                local_locator=True,
                reachable=True,
                load_factor=0.2
            )
        ]

        # Add to map cache
        self.map_cache["10.1.0.0/16"] = MapCacheEntry(
            eid_prefix=EIDPrefix("10.1.0.0", 16, 1),
            rlocs=llama_rlocs + phi3_rlocs,
            ttl=3600,
            authoritative=True,
            created_at=time.time()
        )

        self.map_cache["10.2.0.0/16"] = MapCacheEntry(
            eid_prefix=EIDPrefix("10.2.0.0", 16, 1),
            rlocs=phi3_rlocs,
            ttl=3600,
            authoritative=True,
            created_at=time.time()
        )

        self.map_cache["10.3.0.0/16"] = MapCacheEntry(
            eid_prefix=EIDPrefix("10.3.0.0", 16, 1),
            rlocs=llama_rlocs,
            ttl=3600,
            authoritative=True,
            created_at=time.time()
        )
    
    async def initialize(self):
        """Initialize LISP router services."""
        try:
            # Start control plane listener
            await self._start_control_plane()
            self.running = True
            
            logger.info("LISP router services started successfully")
            
        except Exception as e:
            logger.error("Failed to initialize LISP router", error=str(e))
            raise
    
    async def _start_control_plane(self):
        """Start LISP control plane listener."""
        try:
            # Create UDP socket for LISP control messages (port 4342)
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.control_socket.bind(('0.0.0.0', 4342))
            self.control_socket.setblocking(False)
            
            # Start background task for control message processing
            asyncio.create_task(self._process_control_messages())
            
            logger.info("LISP control plane started on port 4342")
            
        except Exception as e:
            logger.error("Failed to start LISP control plane", error=str(e))
            raise
    
    async def _process_control_messages(self):
        """Process incoming LISP control messages."""
        while self.running:
            try:
                # Non-blocking receive with timeout
                await asyncio.sleep(0.1)
                
                try:
                    data, addr = self.control_socket.recvfrom(1024)
                    await self._handle_control_message(data, addr)
                except socket.error:
                    # No data available, continue
                    continue
                    
            except Exception as e:
                logger.error("Error processing control messages", error=str(e))
                await asyncio.sleep(1)
    
    async def _handle_control_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming LISP control message."""
        try:
            if len(data) < 8:
                logger.warning("Received malformed LISP message", addr=addr)
                return
            
            # Parse LISP header
            header = struct.unpack('!BBHBBH', data[:8])
            msg_type = header[0] & 0xF0 >> 4
            
            logger.debug("Received LISP control message", 
                        type=msg_type, addr=addr, size=len(data))
            
            # Handle different message types
            if msg_type == LISPMessageType.MAP_REQUEST.value:
                await self._handle_map_request(data, addr)
            elif msg_type == LISPMessageType.MAP_REGISTER.value:
                await self._handle_map_register(data, addr)
            
        except Exception as e:
            logger.error("Error handling control message", error=str(e), addr=addr)
    
    async def _handle_map_request(self, data: bytes, addr: Tuple[str, int]):
        """Handle LISP Map Request message."""
        # Simplified map request handling
        logger.info("Processing Map Request", addr=addr)
        # In a full implementation, parse the request and send appropriate reply
    
    async def _handle_map_register(self, data: bytes, addr: Tuple[str, int]):
        """Handle LISP Map Register message."""
        # Simplified map register handling
        logger.info("Processing Map Register", addr=addr)
        # In a full implementation, update map cache with new registrations
    
    async def route_ai_workload(self, workload_type: str, source_eid: str) -> Optional[str]:
        """Route AI workload based on LISP EID-to-RLOC mapping."""
        try:
            # Find matching EID prefix for the source
            matching_prefix = self._find_matching_eid_prefix(source_eid)
            
            if not matching_prefix:
                logger.warning("No matching EID prefix found", source_eid=source_eid)
                return None
            
            # Get map cache entry
            cache_entry = self.map_cache.get(matching_prefix)
            
            if not cache_entry:
                logger.warning("No map cache entry found", prefix=matching_prefix)
                return None
            
            # Check if entry is expired
            if cache_entry.is_expired():
                logger.info("Map cache entry expired, refreshing", prefix=matching_prefix)
                # In production, trigger map request to refresh
                return None
            
            # Get best RLOC for routing
            best_rloc = cache_entry.get_best_rloc()
            
            if not best_rloc:
                logger.warning("No reachable RLOC found", prefix=matching_prefix)
                return None
            
            # Update access statistics
            cache_entry.access_count += 1
            
            logger.info("AI workload routed via LISP", 
                       workload_type=workload_type,
                       source_eid=source_eid,
                       rloc=best_rloc.rloc,
                       prefix=matching_prefix)
            
            return best_rloc.rloc
            
        except Exception as e:
            logger.error("Error routing AI workload", 
                        workload_type=workload_type, 
                        source_eid=source_eid, 
                        error=str(e))
            return None
    
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
                except ValueError:
                    continue
            
            return best_match
            
        except ValueError:
            logger.error("Invalid EID address format", eid=eid)
            return None
    
    async def update_rloc_load(self, rloc: str, load_factor: float):
        """Update load factor for a specific RLOC."""
        try:
            for cache_entry in self.map_cache.values():
                for rloc_mapping in cache_entry.rlocs:
                    if rloc_mapping.rloc == rloc:
                        rloc_mapping.load_factor = load_factor
                        rloc_mapping.last_updated = time.time()
            
            logger.debug("Updated RLOC load factor", rloc=rloc, load_factor=load_factor)
            
        except Exception as e:
            logger.error("Error updating RLOC load", rloc=rloc, error=str(e))
    
    def get_map_cache_stats(self) -> Dict:
        """Get map cache statistics."""
        total_entries = len(self.map_cache)
        expired_entries = sum(1 for entry in self.map_cache.values() if entry.is_expired())
        total_rlocs = sum(len(entry.rlocs) for entry in self.map_cache.values())
        reachable_rlocs = sum(
            sum(1 for rloc in entry.rlocs if rloc.reachable) 
            for entry in self.map_cache.values()
        )
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "total_rlocs": total_rlocs,
            "reachable_rlocs": reachable_rlocs,
            "cache_hit_ratio": self._calculate_cache_hit_ratio()
        }
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio based on access patterns."""
        total_accesses = sum(entry.access_count for entry in self.map_cache.values())
        return 0.95 if total_accesses == 0 else min(0.95, total_accesses / (total_accesses + 10))
    
    async def cleanup(self):
        """Clean up LISP router resources."""
        self.running = False
        
        if self.control_socket:
            self.control_socket.close()
            
        logger.info("LISP router cleaned up")