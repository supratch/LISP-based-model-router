#!/usr/bin/env python3
"""
DNS-based Router for AI Workload Distribution
Implements DNS-based load balancing and service discovery for AI models.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import ipaddress
import random

import dns.resolver
import dns.rdatatype
import dns.message
import dns.query
import dns.zone
import dns.name
from dns import resolver

import structlog

logger = structlog.get_logger(__name__)


class ServiceState(Enum):
    """Service health states for DNS routing."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DNSServiceRecord:
    """DNS service record for AI model endpoints."""
    name: str
    address: str
    port: int
    weight: int
    priority: int
    ttl: int = 300
    state: ServiceState = ServiceState.UNKNOWN
    last_check: float = 0.0
    response_time: float = 0.0
    error_count: int = 0
    success_count: int = 0
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.last_check == 0.0:
            self.last_check = time.time()
    
    @property
    def fqdn(self) -> str:
        """Get fully qualified domain name."""
        return f"{self.name}.ai-workload.local"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0.0
    
    def is_healthy(self) -> bool:
        """Check if service is healthy based on state and metrics."""
        return (
            self.state == ServiceState.HEALTHY and 
            self.success_rate >= 80 and 
            self.response_time < 5.0
        )


@dataclass
class DNSZoneConfig:
    """DNS zone configuration for AI services."""
    zone_name: str
    authoritative_ns: List[str]
    admin_email: str
    refresh: int = 3600
    retry: int = 1800
    expire: int = 604800
    minimum: int = 300


class DNSRouter:
    """DNS-based router for AI workload distribution."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize DNS router with configuration."""
        self.config = config or {}
        self.service_records: Dict[str, List[DNSServiceRecord]] = {}
        self.zone_config = DNSZoneConfig(
            zone_name="ai-workload.local",
            authoritative_ns=["ns1.ai-workload.local", "ns2.ai-workload.local"],
            admin_email="admin.ai-workload.local"
        )
        self.resolver = dns.resolver.Resolver()
        self.running = False
        self.health_check_interval = 30  # seconds
        
        # Initialize AI model service records
        self._initialize_ai_services()
        
        logger.info("DNS router initialized", 
                   zone=self.zone_config.zone_name,
                   services=list(self.service_records.keys()))
    
    def _initialize_ai_services(self):
        """Initialize DNS service records for AI models (local models only)."""
        # Llama 3.2 Local service records
        self.service_records["llama32local"] = [
            DNSServiceRecord(
                name="llama32-local-primary",
                address="127.0.0.1",
                port=11434,
                weight=100,
                priority=10,
                state=ServiceState.HEALTHY
            )
        ]

        # Phi-3 Local service records
        self.service_records["phi3local"] = [
            DNSServiceRecord(
                name="phi3-local-primary",
                address="127.0.0.1",
                port=11434,
                weight=100,
                priority=10,
                state=ServiceState.HEALTHY
            )
        ]
    
    async def initialize(self):
        """Initialize DNS router services."""
        try:
            # Configure DNS resolver
            await self._setup_resolver()
            
            # Start health checking
            await self._start_health_checks()
            
            # Start DNS server (simplified simulation)
            await self._start_dns_server()
            
            self.running = True
            logger.info("DNS router services started successfully")
            
        except Exception as e:
            logger.error("Failed to initialize DNS router", error=str(e))
            raise
    
    async def _setup_resolver(self):
        """Setup DNS resolver configuration."""
        try:
            # Configure custom nameservers for AI services
            self.resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Fallback to public DNS
            self.resolver.timeout = 2
            self.resolver.lifetime = 5
            
            logger.info("DNS resolver configured", nameservers=self.resolver.nameservers)
            
        except Exception as e:
            logger.error("Failed to setup DNS resolver", error=str(e))
            raise
    
    async def _start_health_checks(self):
        """Start background health checking for all services."""
        logger.info("🚀 Starting health check service",
                   interval_seconds=self.health_check_interval,
                   total_services=len(self.service_records),
                   total_records=sum(len(records) for records in self.service_records.values()))

        # Log initial service states
        for service_name, records in self.service_records.items():
            logger.info("📋 Initial service configuration",
                       service=service_name,
                       records=[{
                           "name": r.name,
                           "address": f"{r.address}:{r.port}",
                           "initial_state": r.state.value
                       } for r in records])

        asyncio.create_task(self._health_check_loop())
        logger.info("✅ Health check service started successfully")
    
    async def _health_check_loop(self):
        """Continuous health checking loop."""
        check_iteration = 0
        while self.running:
            try:
                check_iteration += 1
                logger.info("🔄 Starting health check iteration",
                           iteration=check_iteration,
                           total_services=len(self.service_records),
                           interval_seconds=self.health_check_interval)

                for service_name, records in self.service_records.items():
                    logger.info("🔍 Checking service",
                               service=service_name,
                               total_records=len(records))

                    for record in records:
                        await self._check_service_health(record)

                # Log summary after all checks
                total_healthy = sum(1 for records in self.service_records.values()
                                  for r in records if r.state == ServiceState.HEALTHY)
                total_degraded = sum(1 for records in self.service_records.values()
                                   for r in records if r.state == ServiceState.DEGRADED)
                total_unhealthy = sum(1 for records in self.service_records.values()
                                    for r in records if r.state == ServiceState.UNHEALTHY)

                logger.info("📊 Health check iteration complete",
                           iteration=check_iteration,
                           healthy=total_healthy,
                           degraded=total_degraded,
                           unhealthy=total_unhealthy,
                           next_check_in_seconds=self.health_check_interval)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error("💥 Error in health check loop",
                           iteration=check_iteration,
                           error_type=type(e).__name__,
                           error=str(e),
                           traceback=True)
                await asyncio.sleep(5)
    
    async def _check_service_health(self, record: DNSServiceRecord):
        """Check health of a specific service record."""
        try:
            start_time = time.time()

            # Log health check start
            logger.info("🔍 Starting health check",
                       service=record.name,
                       address=record.address,
                       port=record.port,
                       current_state=record.state.value,
                       success_count=record.success_count,
                       error_count=record.error_count)

            # Simulate health check (in production, use actual HTTP/TCP health checks)
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=3)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    # Use Ollama's /api/tags endpoint for health check
                    health_url = f"http://{record.address}:{record.port}/api/tags"

                    logger.info("📡 Sending health check request",
                               service=record.name,
                               url=health_url,
                               timeout=3)

                    async with session.get(health_url) as response:
                        response_time = time.time() - start_time

                        logger.info("📥 Received health check response",
                                   service=record.name,
                                   status_code=response.status,
                                   response_time_ms=round(response_time * 1000, 2))

                        if response.status == 200:
                            old_state = record.state
                            record.state = ServiceState.HEALTHY
                            record.success_count += 1

                            logger.info("✅ Service is HEALTHY",
                                       service=record.name,
                                       old_state=old_state.value,
                                       new_state=record.state.value,
                                       success_count=record.success_count,
                                       response_time_ms=round(response_time * 1000, 2))
                        else:
                            old_state = record.state
                            record.state = ServiceState.DEGRADED
                            record.error_count += 1

                            logger.warning("⚠️ Service is DEGRADED",
                                          service=record.name,
                                          old_state=old_state.value,
                                          new_state=record.state.value,
                                          status_code=response.status,
                                          error_count=record.error_count)

                        record.response_time = response_time
                        record.last_check = time.time()

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    # Service unreachable or timeout
                    old_state = record.state
                    record.state = ServiceState.UNHEALTHY
                    record.error_count += 1
                    record.response_time = time.time() - start_time
                    record.last_check = time.time()

                    logger.error("❌ Service is UNHEALTHY",
                               service=record.name,
                               old_state=old_state.value,
                               new_state=record.state.value,
                               address=f"{record.address}:{record.port}",
                               error_type=type(e).__name__,
                               error=str(e),
                               error_count=record.error_count,
                               response_time_ms=round(record.response_time * 1000, 2))

            # Log final health check summary
            logger.info("🏁 Health check completed",
                        service=record.name,
                        final_state=record.state.value,
                        response_time_ms=round(record.response_time * 1000, 2),
                        success_rate=f"{record.success_rate:.1f}%",
                        total_checks=record.success_count + record.error_count)

        except Exception as e:
            logger.error("💥 Health check EXCEPTION",
                        service=record.name,
                        error_type=type(e).__name__,
                        error=str(e),
                        traceback=True)
            record.state = ServiceState.UNKNOWN
            record.error_count += 1
            record.last_check = time.time()
    
    async def _start_dns_server(self):
        """Start simplified DNS server for AI service resolution."""
        # In production, implement full DNS server
        # For now, simulate DNS responses
        logger.info("DNS server simulation started")
    
    async def resolve_ai_service(self, service_name: str, query_type: str = "A") -> Optional[DNSServiceRecord]:
        """Resolve AI service using DNS-based load balancing."""
        try:
            logger.info("🔎 Resolving AI service via DNS",
                       service=service_name,
                       query_type=query_type)

            records = self.service_records.get(service_name, [])

            if not records:
                logger.warning("❌ No DNS records found for service", service=service_name)
                return None

            # Log all available records
            logger.info("📋 Available DNS records",
                       service=service_name,
                       total_records=len(records),
                       records=[{
                           "name": r.name,
                           "address": f"{r.address}:{r.port}",
                           "state": r.state.value,
                           "success_rate": f"{r.success_rate:.1f}%",
                           "response_time_ms": round(r.response_time * 1000, 2)
                       } for r in records])

            # Filter healthy records
            healthy_records = [r for r in records if r.is_healthy()]

            logger.info("🏥 Health filtering results",
                       service=service_name,
                       total_records=len(records),
                       healthy_records=len(healthy_records),
                       healthy_names=[r.name for r in healthy_records])

            if not healthy_records:
                # Fall back to degraded services if no healthy ones
                degraded_records = [r for r in records if r.state == ServiceState.DEGRADED]
                unhealthy_records = [r for r in records if r.state == ServiceState.UNHEALTHY]

                logger.warning("⚠️ No healthy records available",
                              service=service_name,
                              degraded_count=len(degraded_records),
                              unhealthy_count=len(unhealthy_records),
                              degraded_names=[r.name for r in degraded_records],
                              unhealthy_names=[r.name for r in unhealthy_records])

                if degraded_records:
                    healthy_records = degraded_records
                    logger.warning("🔄 Using degraded services as fallback",
                                 service=service_name,
                                 degraded_records=[{
                                     "name": r.name,
                                     "address": f"{r.address}:{r.port}",
                                     "state": r.state.value,
                                     "success_rate": f"{r.success_rate:.1f}%"
                                 } for r in degraded_records])
                else:
                    logger.error("❌ No usable records found for service",
                               service=service_name,
                               all_states=[r.state.value for r in records])
                    return None

            # Implement weighted round-robin selection
            selected_record = self._weighted_selection(healthy_records)

            if selected_record:
                logger.info("✅ Service resolved successfully",
                           service=service_name,
                           selected_record=selected_record.name,
                           address=f"{selected_record.address}:{selected_record.port}",
                           state=selected_record.state.value,
                           success_rate=f"{selected_record.success_rate:.1f}%",
                           response_time_ms=round(selected_record.response_time * 1000, 2))
            else:
                logger.error("❌ Failed to select a record",
                           service=service_name,
                           available_records=len(healthy_records))

            return selected_record

        except Exception as e:
            logger.error("💥 Error resolving AI service",
                        service=service_name,
                        error_type=type(e).__name__,
                        error=str(e),
                        traceback=True)
            return None
    
    def _weighted_selection(self, records: List[DNSServiceRecord]) -> Optional[DNSServiceRecord]:
        """Select record using weighted random selection based on priority and weight."""
        if not records:
            return None
        
        # Sort by priority (lower is better)
        records.sort(key=lambda r: r.priority)
        
        # Get records with the same (best) priority
        best_priority = records[0].priority
        same_priority_records = [r for r in records if r.priority == best_priority]
        
        if len(same_priority_records) == 1:
            return same_priority_records[0]
        
        # Weighted selection among same priority records
        total_weight = sum(r.weight for r in same_priority_records)
        
        if total_weight == 0:
            return random.choice(same_priority_records)
        
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for record in same_priority_records:
            current_weight += record.weight
            if rand_val <= current_weight:
                return record
        
        return same_priority_records[0]
    
    async def update_service_weight(self, service_name: str, record_name: str, new_weight: int):
        """Update weight for a specific service record."""
        try:
            records = self.service_records.get(service_name, [])
            
            for record in records:
                if record.name == record_name:
                    old_weight = record.weight
                    record.weight = max(0, min(100, new_weight))  # Clamp between 0-100
                    
                    logger.info("Service weight updated",
                               service=service_name,
                               record=record_name,
                               old_weight=old_weight,
                               new_weight=record.weight)
                    return
            
            logger.warning("Service record not found for weight update",
                          service=service_name, record=record_name)
                          
        except Exception as e:
            logger.error("Error updating service weight", 
                        service=service_name, record=record_name, error=str(e))
    
    def get_service_stats(self) -> Dict:
        """Get DNS service statistics."""
        stats = {
            "total_services": len(self.service_records),
            "total_records": sum(len(records) for records in self.service_records.values()),
            "services": {}
        }
        
        for service_name, records in self.service_records.items():
            healthy_count = sum(1 for r in records if r.state == ServiceState.HEALTHY)
            degraded_count = sum(1 for r in records if r.state == ServiceState.DEGRADED)
            unhealthy_count = sum(1 for r in records if r.state == ServiceState.UNHEALTHY)
            
            avg_response_time = (
                sum(r.response_time for r in records) / len(records) 
                if records else 0
            )
            
            stats["services"][service_name] = {
                "total_records": len(records),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "avg_response_time": avg_response_time,
                "records": [
                    {
                        "name": r.name,
                        "address": r.address,
                        "state": r.state.value,
                        "success_rate": r.success_rate,
                        "response_time": r.response_time
                    }
                    for r in records
                ]
            }
        
        return stats
    
    async def perform_dns_lookup(self, hostname: str, record_type: str = "A") -> List[str]:
        """Perform actual DNS lookup for external services."""
        try:
            if record_type.upper() == "A":
                rdtype = dns.rdatatype.A
            elif record_type.upper() == "AAAA":
                rdtype = dns.rdatatype.AAAA
            elif record_type.upper() == "CNAME":
                rdtype = dns.rdatatype.CNAME
            else:
                rdtype = dns.rdatatype.A
            
            answers = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.resolver.resolve(hostname, rdtype)
            )
            
            results = [str(answer) for answer in answers]
            
            logger.debug("DNS lookup completed", 
                        hostname=hostname, 
                        record_type=record_type, 
                        results=results)
            
            return results
            
        except Exception as e:
            logger.error("DNS lookup failed", hostname=hostname, error=str(e))
            return []
    
    async def cleanup(self):
        """Clean up DNS router resources."""
        self.running = False
        logger.info("DNS router cleaned up")