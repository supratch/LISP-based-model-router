#!/usr/bin/env python3
"""
API Routes for AI Workload Routing System
Provides REST endpoints for routing management and monitoring.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

# Router instance
router = APIRouter()

# Import routing services (will be injected by main app)
from app.routing.lisp_router import LISPRouter
from app.routing.dns_router import DNSRouter
from app.models.llm_router import LLMRouter
from app.routing.lisp_packet import get_packet_generator, LISPPacket
from app.routing.pcap_writer import PCAPWriter, create_pcap_from_packet_dicts


# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    """Request model for query routing."""
    query: str = Field(..., description="The query to be routed")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for routing")
    priority: Optional[str] = Field(default="medium", description="Query priority (low, medium, high)")
    source_eid: Optional[str] = Field(default="10.1.0.1", description="Source EID for LISP routing")
    preferred_model: Optional[str] = Field(default=None, description="Preferred LLM model if available")


class RoutingResponse(BaseModel):
    """Response model for query routing."""
    selected_model: str
    routing_method: str
    endpoint: str
    confidence_score: float
    reasoning: str
    estimated_cost: float
    estimated_response_time: float
    alternative_models: List[str]
    routing_metadata: Dict[str, Any]
    lisp_packet: Optional[Dict[str, Any]] = Field(default=None, description="LISP packet information")
    llm_response: Optional[str] = Field(default=None, description="Generated response from the LLM model")
    generation_time: Optional[float] = Field(default=None, description="Time taken to generate response in seconds")


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    uptime_seconds: float


class StatsResponse(BaseModel):
    """Response model for system statistics."""
    lisp_stats: Dict[str, Any]
    dns_stats: Dict[str, Any]
    llm_stats: Dict[str, Any]
    system_stats: Dict[str, Any]


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    service: str = Field(..., description="Service to update (lisp, dns, llm)")
    config: Dict[str, Any] = Field(..., description="New configuration parameters")


# Dependency injection for routing services
async def get_lisp_router() -> LISPRouter:
    """Get LISP router instance."""
    # This will be overridden by main app to inject actual instance
    from app.main import lisp_router
    if not lisp_router:
        raise HTTPException(status_code=503, detail="LISP router not available")
    return lisp_router


async def get_dns_router() -> DNSRouter:
    """Get DNS router instance."""
    from app.main import dns_router
    if not dns_router:
        raise HTTPException(status_code=503, detail="DNS router not available")
    return dns_router


async def get_llm_router() -> LLMRouter:
    """Get LLM router instance."""
    from app.main import llm_router
    if not llm_router:
        raise HTTPException(status_code=503, detail="LLM router not available")
    return llm_router


# API Endpoints
@router.post("/route", response_model=RoutingResponse)
async def route_query(
    request: QueryRequest,
    lisp_router: LISPRouter = Depends(get_lisp_router),
    dns_router: DNSRouter = Depends(get_dns_router),
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """Route a query to the appropriate AI model using LISP and DNS routing."""
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Step 1: Analyze query and determine best LLM model
        routing_decision = await llm_router.route_query(
            request.query, 
            request.context or {}
        )
        
        # Step 2: Use LISP routing to find model endpoint
        lisp_endpoint = await lisp_router.route_ai_workload(
            routing_decision.selected_model,
            request.source_eid
        )
        
        # Step 3: Use DNS routing for service discovery and load balancing
        dns_record = await dns_router.resolve_ai_service(
            routing_decision.selected_model.replace("-", "").replace(".", "")
        )
        
        # Determine final endpoint
        final_endpoint = lisp_endpoint or (dns_record.address if dns_record else None)
        
        if not final_endpoint:
            raise HTTPException(
                status_code=503, 
                detail=f"No available endpoint for model {routing_decision.selected_model}"
            )
        
        # Determine routing method used
        routing_method = []
        if lisp_endpoint:
            routing_method.append("LISP")
        if dns_record:
            routing_method.append("DNS")
        
        routing_metadata = {
            "query_analysis": {
                "estimated_tokens": getattr(await llm_router.analyze_query(request.query), 'estimated_tokens', 0),
                "complexity_score": getattr(await llm_router.analyze_query(request.query), 'complexity_score', 0.0),
                "query_type": getattr(await llm_router.analyze_query(request.query), 'query_type', '').value if hasattr(getattr(await llm_router.analyze_query(request.query), 'query_type', ''), 'value') else 'unknown'
            },
            "lisp_routing": {
                "source_eid": request.source_eid,
                "endpoint": lisp_endpoint,
                "used": bool(lisp_endpoint)
            },
            "dns_routing": {
                "service_name": routing_decision.selected_model.replace("-", "").replace(".", ""),
                "record_name": dns_record.name if dns_record else None,
                "address": dns_record.address if dns_record else None,
                "port": dns_record.port if dns_record else None,
                "used": bool(dns_record)
            },
            "processing_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
        }
        
        # Step 4: Generate LISP packet post-routing
        packet_generator = get_packet_generator()
        import hashlib
        query_hash = hashlib.md5(request.query.encode()).hexdigest()[:8]

        lisp_packet = packet_generator.generate_ai_query_packet(
            source_eid=request.source_eid,
            routing_decision={
                "selected_model": routing_decision.selected_model,
                "endpoint": final_endpoint,
                "routing_metadata": routing_metadata
            },
            query=request.query,
            query_hash=query_hash
        )

        # Step 5: Generate response from the selected model (if it's a local model)
        llm_response = None
        generation_time = None

        if routing_decision.selected_model in ["llama3.2-local", "phi3-local"]:
            try:
                from ..models.ollama_client import get_ollama_client
                generation_start = asyncio.get_event_loop().time()

                ollama_client = get_ollama_client()

                # Map model names to Ollama model IDs
                model_id_map = {
                    "llama3.2-local": "llama3.2:3b",
                    "phi3-local": "phi3:mini"
                }
                model_id = model_id_map.get(routing_decision.selected_model, "llama3.2:3b")

                # Generate response
                result = await ollama_client.generate(
                    model=model_id,
                    prompt=request.query,
                    stream=False
                )

                llm_response = result.get("response", "")
                generation_time = asyncio.get_event_loop().time() - generation_start

                logger.info("LLM response generated",
                           model=routing_decision.selected_model,
                           generation_time=generation_time,
                           response_length=len(llm_response))

            except Exception as e:
                logger.error("Error generating LLM response", error=str(e))
                llm_response = f"[Error generating response: {str(e)}]"
                generation_time = 0.0
        else:
            llm_response = f"[Model {routing_decision.selected_model} is not a local model - actual generation would be sent to external endpoint {final_endpoint}]"
            generation_time = 0.0

        response = RoutingResponse(
            selected_model=routing_decision.selected_model,
            routing_method=" + ".join(routing_method) or "Direct",
            endpoint=final_endpoint,
            confidence_score=routing_decision.confidence_score,
            reasoning=routing_decision.reasoning,
            estimated_cost=routing_decision.estimated_cost,
            estimated_response_time=routing_decision.estimated_response_time,
            alternative_models=routing_decision.alternative_models,
            routing_metadata=routing_metadata,
            lisp_packet=lisp_packet.to_dict(),
            llm_response=llm_response,
            generation_time=generation_time
        )

        logger.info("Query routed successfully",
                   model=routing_decision.selected_model,
                   endpoint=final_endpoint,
                   method=response.routing_method,
                   packet_id=lisp_packet.packet_id,
                   has_llm_response=llm_response is not None)

        return response
        
    except Exception as e:
        logger.error("Error routing query", error=str(e))
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    lisp_router: LISPRouter = Depends(get_lisp_router),
    dns_router: DNSRouter = Depends(get_dns_router),
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """Get health status of all routing services."""
    try:
        services = {
            "lisp_router": "healthy" if lisp_router.running else "unhealthy",
            "dns_router": "healthy" if dns_router.running else "unhealthy",
            "llm_router": "healthy" if llm_router.running else "unhealthy"
        }
        
        overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "degraded"
        
        # Calculate uptime (simplified)
        import time
        uptime = time.time() - getattr(health_check, 'start_time', time.time())
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            services=services,
            uptime_seconds=uptime
        )
        
    except Exception as e:
        logger.error("Error checking health", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(
    lisp_router: LISPRouter = Depends(get_lisp_router),
    dns_router: DNSRouter = Depends(get_dns_router),
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """Get comprehensive statistics from all routing services."""
    try:
        import psutil
        import traceback

        # Get stats from each router with individual error handling
        try:
            lisp_stats = lisp_router.get_map_cache_stats()
        except Exception as e:
            logger.error("Error getting LISP stats", error=str(e), exc_info=True)
            lisp_stats = {"error": "Failed to retrieve LISP stats"}

        try:
            dns_stats = dns_router.get_service_stats()
        except Exception as e:
            logger.error("Error getting DNS stats", error=str(e), exc_info=True)
            dns_stats = {"error": "Failed to retrieve DNS stats"}

        try:
            llm_stats = llm_router.get_routing_stats()
        except Exception as e:
            logger.error("Error getting LLM stats", error=str(e), exc_info=True)
            llm_stats = {"error": "Failed to retrieve LLM stats"}

        # System statistics - use non-blocking calls
        try:
            system_stats = {
                "cpu_usage_percent": psutil.cpu_percent(interval=0),  # Non-blocking
                "memory_usage_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "active_processes": len(psutil.pids())
            }

            # Try to get network connections, but handle permission errors
            try:
                system_stats["network_connections"] = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # macOS requires special permissions for network connections
                system_stats["network_connections"] = "N/A (requires elevated permissions)"

        except Exception as e:
            logger.error("Error getting system stats", error=str(e), exc_info=True)
            system_stats = {"error": "Failed to retrieve system stats"}

        return StatsResponse(
            lisp_stats=lisp_stats,
            dns_stats=dns_stats,
            llm_stats=llm_stats,
            system_stats=system_stats
        )

    except Exception as e:
        logger.error("Error getting statistics", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@router.get("/models")
async def list_models(
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """List available AI models and their status."""
    try:
        models_info = {}
        
        for model_name, model in llm_router.models.items():
            models_info[model_name] = {
                "name": model.name,
                "endpoint": model.endpoint,
                "model_id": model.model_id,
                "available": model.available,
                "current_load": model.current_load,
                "max_tokens": model.max_tokens,
                "cost_per_token": model.cost_per_token,
                "avg_response_time": model.avg_response_time,
                "rate_limit": model.rate_limit,
                "current_requests": model.current_requests,
                "capabilities": {qt.value: cap.value for qt, cap in model.capabilities.items()}
            }
        
        return {"models": models_info}
        
    except Exception as e:
        logger.error("Error listing models", error=str(e))
        raise HTTPException(status_code=500, detail="Model listing failed")


@router.post("/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    lisp_router: LISPRouter = Depends(get_lisp_router),
    dns_router: DNSRouter = Depends(get_dns_router),
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """Update configuration for routing services."""
    try:
        if request.service == "lisp":
            # Update LISP router configuration
            # In production, implement proper config updates
            logger.info("LISP configuration update requested", config=request.config)
            return {"message": "LISP configuration updated", "service": "lisp"}
            
        elif request.service == "dns":
            # Update DNS router configuration
            logger.info("DNS configuration update requested", config=request.config)
            return {"message": "DNS configuration updated", "service": "dns"}
            
        elif request.service == "llm":
            # Update LLM router configuration
            if "load_balancing_weights" in request.config:
                llm_router.load_balancing_weights.update(request.config["load_balancing_weights"])
            
            logger.info("LLM configuration updated", config=request.config)
            return {"message": "LLM configuration updated", "service": "llm"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {request.service}")
            
    except Exception as e:
        logger.error("Error updating configuration", service=request.service, error=str(e))
        raise HTTPException(status_code=500, detail="Configuration update failed")


@router.post("/services/{service_name}/weight")
async def update_service_weight(
    service_name: str,
    record_name: str = Query(..., description="DNS record name to update"),
    weight: int = Query(..., ge=0, le=100, description="New weight (0-100)"),
    dns_router: DNSRouter = Depends(get_dns_router)
):
    """Update weight for a specific DNS service record."""
    try:
        await dns_router.update_service_weight(service_name, record_name, weight)
        
        return {
            "message": "Service weight updated",
            "service": service_name,
            "record": record_name,
            "new_weight": weight
        }
        
    except Exception as e:
        logger.error("Error updating service weight", 
                    service=service_name, record=record_name, error=str(e))
        raise HTTPException(status_code=500, detail="Weight update failed")


@router.get("/metrics")
async def get_metrics(
    lisp_router: LISPRouter = Depends(get_lisp_router),
    dns_router: DNSRouter = Depends(get_dns_router),
    llm_router: LLMRouter = Depends(get_llm_router)
):
    """Get metrics in Prometheus format for monitoring."""
    try:
        from prometheus_client import generate_latest, CollectorRegistry, Counter, Gauge, Histogram
        
        # Create custom registry
        registry = CollectorRegistry()
        
        # Define metrics
        query_total = Counter('ai_routing_queries_total', 'Total queries routed', 
                            ['model', 'method'], registry=registry)
        model_load = Gauge('ai_model_load', 'Current model load', ['model'], registry=registry)
        response_time = Histogram('ai_routing_response_time_seconds', 'Response time', 
                                ['model'], registry=registry)
        
        # Populate metrics with current data
        llm_stats = llm_router.get_routing_stats()

        return Response(content=generate_latest(registry), media_type="text/plain")

    except ImportError:
        raise HTTPException(status_code=501, detail="Prometheus client not installed")
    except Exception as e:
        logger.error("Error generating metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packets/stats")
async def get_packet_stats():
    """Get LISP packet generation statistics."""
    try:
        packet_generator = get_packet_generator()
        stats = packet_generator.get_packet_stats()

        return JSONResponse(content={
            "status": "success",
            "stats": stats
        })

    except Exception as e:
        logger.error("Error getting packet stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packets/recent")
async def get_recent_packets(count: int = Query(default=10, ge=1, le=100)):
    """Get recent LISP packets."""
    try:
        packet_generator = get_packet_generator()
        packets = packet_generator.get_recent_packets(count)

        return JSONResponse(content={
            "status": "success",
            "count": len(packets),
            "packets": packets
        })

    except Exception as e:
        logger.error("Error getting recent packets", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packets/{packet_id}")
async def get_packet_details(packet_id: str):
    """Get detailed information about a specific LISP packet."""
    try:
        packet_generator = get_packet_generator()

        # Find packet in history
        packet = None
        for p in packet_generator.packet_history:
            if p.packet_id == packet_id:
                packet = p
                break

        if not packet:
            raise HTTPException(status_code=404, detail=f"Packet {packet_id} not found")

        # Generate visualization
        visualization = packet_generator.visualize_packet(packet)

        return JSONResponse(content={
            "status": "success",
            "packet": packet.to_dict(),
            "visualization": visualization
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting packet details", packet_id=packet_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packets/visualize")
async def visualize_last_packet():
    """Visualize the most recent LISP packet."""
    try:
        packet_generator = get_packet_generator()

        if not packet_generator.packet_history:
            raise HTTPException(status_code=404, detail="No packets generated yet")

        last_packet = packet_generator.packet_history[-1]
        visualization = packet_generator.visualize_packet(last_packet)

        return JSONResponse(content={
            "status": "success",
            "packet_id": last_packet.packet_id,
            "visualization": visualization,
            "packet_data": last_packet.to_dict()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error visualizing packet", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packets/download/pcap")
async def download_all_packets_pcap(count: int = Query(default=10, ge=1, le=100)):
    """Download recent LISP packets as PCAP file."""
    try:
        packet_generator = get_packet_generator()

        if not packet_generator.packet_history:
            raise HTTPException(status_code=404, detail="No packets available for download")

        # Get recent packets
        recent_packets = packet_generator.packet_history[-count:] if len(packet_generator.packet_history) >= count else packet_generator.packet_history

        # Create PCAP file
        pcap_writer = PCAPWriter()
        pcap_data = pcap_writer.create_pcap_from_packets(recent_packets)

        # Generate filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lisp_packets_{timestamp}.pcap"

        logger.info("PCAP file generated for download",
                   packets=len(recent_packets),
                   size=len(pcap_data),
                   filename=filename)

        return Response(
            content=pcap_data,
            media_type="application/vnd.tcpdump.pcap",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pcap_data))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating PCAP file", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packets/{packet_id}/download/pcap")
async def download_single_packet_pcap(packet_id: str):
    """Download a specific LISP packet as PCAP file."""
    try:
        packet_generator = get_packet_generator()

        # Find packet in history
        packet = None
        for p in packet_generator.packet_history:
            if p.packet_id == packet_id:
                packet = p
                break

        if not packet:
            raise HTTPException(status_code=404, detail=f"Packet {packet_id} not found")

        # Create PCAP file with single packet
        pcap_writer = PCAPWriter()
        pcap_data = pcap_writer.create_pcap_from_packets([packet])

        filename = f"lisp_packet_{packet_id}.pcap"

        logger.info("Single packet PCAP generated",
                   packet_id=packet_id,
                   size=len(pcap_data))

        return Response(
            content=pcap_data,
            media_type="application/vnd.tcpdump.pcap",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pcap_data))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating single packet PCAP", packet_id=packet_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        
        for model_name, model_data in llm_stats.get('models', {}).items():
            model_load.labels(model=model_name).set(model_data.get('current_load', 0))
            
            # Add query count (simplified)
            query_total.labels(model=model_name, method='auto').inc(
                model_data.get('total_queries_routed', 0)
            )
        
        # Return metrics in Prometheus format
        return Response(generate_latest(registry), media_type="text/plain")
        
    except Exception as e:
        logger.error("Error generating metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics generation failed")


# Set startup time for uptime calculation
import time
health_check.start_time = time.time()