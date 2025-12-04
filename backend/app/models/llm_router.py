#!/usr/bin/env python3
"""
LLM Router for Intelligent AI Model Selection
Routes queries to appropriate LLM models based on query analysis and load balancing.
"""

import asyncio
import json
import time
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

import structlog
from .ollama_client import OllamaClient

logger = structlog.get_logger(__name__)


class QueryType(Enum):
    """Types of queries for LLM routing decisions."""
    SIMPLE_QA = "simple_qa"
    COMPLEX_REASONING = "complex_reasoning"
    CODE_GENERATION = "code_generation"
    CREATIVE_WRITING = "creative_writing"
    DATA_ANALYSIS = "data_analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    MATH_COMPUTATION = "math_computation"
    GENERAL = "general"


class ModelCapability(Enum):
    """Model capability levels for different tasks."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class LLMModel:
    """LLM model configuration and capabilities."""
    name: str
    endpoint: str
    model_id: str
    max_tokens: int
    cost_per_token: float
    avg_response_time: float
    capabilities: Dict[QueryType, ModelCapability]
    current_load: float = 0.0
    available: bool = True
    rate_limit: int = 100  # requests per minute
    current_requests: int = 0
    last_request_time: float = 0.0
    
    def __post_init__(self):
        """Initialize request tracking."""
        if self.last_request_time == 0.0:
            self.last_request_time = time.time()
    
    def can_handle_request(self) -> bool:
        """Check if model can handle new request based on rate limits."""
        current_time = time.time()
        time_window = 60  # 1 minute window
        
        # Reset counter if outside time window
        if current_time - self.last_request_time > time_window:
            self.current_requests = 0
            self.last_request_time = current_time
        
        return self.available and self.current_requests < self.rate_limit
    
    def record_request(self):
        """Record a new request for rate limiting."""
        self.current_requests += 1
        self.last_request_time = time.time()


@dataclass
class QueryAnalysis:
    """Analysis results for incoming queries."""
    query_type: QueryType
    complexity_score: float  # 0.0 to 1.0
    estimated_tokens: int
    priority: str  # high, medium, low
    requires_reasoning: bool
    requires_creativity: bool
    language: str = "en"
    
    @property
    def is_complex(self) -> bool:
        """Check if query is considered complex."""
        return self.complexity_score > 0.7 or self.requires_reasoning


@dataclass
class RoutingDecision:
    """LLM routing decision with reasoning."""
    selected_model: str
    confidence_score: float
    reasoning: str
    alternative_models: List[str]
    estimated_cost: float
    estimated_response_time: float
    load_factor: float


class LLMRouter:
    """Intelligent router for LLM model selection."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize LLM router with model configurations."""
        self.config = config or {}
        self.models: Dict[str, LLMModel] = {}
        self.query_history: List[Tuple[str, str, float]] = []  # (query_hash, model, response_time)
        self.routing_stats: Dict[str, Dict] = {}
        self.running = False

        # Initialize Ollama client for local LLMs
        self.ollama_client = OllamaClient()

        # Initialize AI models
        self._initialize_models()

        # Load balancing weights - prioritize capability for demo
        self.load_balancing_weights = {
            "capability": 0.6,  # Increased to prioritize model capabilities
            "load": 0.2,
            "cost": 0.1,  # Reduced cost weight for demo
            "response_time": 0.1
        }

        logger.info("LLM router initialized", models=list(self.models.keys()))
    
    def _initialize_models(self):
        """Initialize available LLM models with their capabilities."""
        # Local Ollama Models - Primary models for all queries
        # Llama 3.2 3B - Excellent general-purpose model
        self.models["llama3.2-local"] = LLMModel(
            name="Llama-3.2-3B (Local)",
            endpoint="localhost:11434",
            model_id="llama3.2:3b",
            max_tokens=2048,
            cost_per_token=0.0,  # Free - running locally
            avg_response_time=0.8,  # Fast on local hardware
            capabilities={
                QueryType.SIMPLE_QA: ModelCapability.EXCELLENT,
                QueryType.COMPLEX_REASONING: ModelCapability.GOOD,
                QueryType.CODE_GENERATION: ModelCapability.GOOD,
                QueryType.CREATIVE_WRITING: ModelCapability.EXCELLENT,
                QueryType.DATA_ANALYSIS: ModelCapability.GOOD,
                QueryType.SUMMARIZATION: ModelCapability.EXCELLENT,
                QueryType.TRANSLATION: ModelCapability.GOOD,
                QueryType.MATH_COMPUTATION: ModelCapability.GOOD,
                QueryType.GENERAL: ModelCapability.EXCELLENT
            },
            rate_limit=1000,  # High rate limit for local model
            available=True  # Always available if Ollama is running
        )

        # Phi-3 Mini - Excellent for code generation and math
        self.models["phi3-local"] = LLMModel(
            name="Phi-3-Mini (Local)",
            endpoint="localhost:11434",
            model_id="phi3:mini",
            max_tokens=2048,
            cost_per_token=0.0,  # Free - running locally
            avg_response_time=0.6,  # Very fast
            capabilities={
                QueryType.SIMPLE_QA: ModelCapability.GOOD,
                QueryType.COMPLEX_REASONING: ModelCapability.GOOD,
                QueryType.CODE_GENERATION: ModelCapability.EXCELLENT,  # Phi-3 excels at code
                QueryType.CREATIVE_WRITING: ModelCapability.FAIR,
                QueryType.DATA_ANALYSIS: ModelCapability.GOOD,
                QueryType.SUMMARIZATION: ModelCapability.GOOD,
                QueryType.TRANSLATION: ModelCapability.FAIR,
                QueryType.MATH_COMPUTATION: ModelCapability.EXCELLENT,  # Phi-3 excels at math
                QueryType.GENERAL: ModelCapability.GOOD
            },
            rate_limit=1000,
            available=True
        )

        # Initialize routing statistics
        for model_name in self.models.keys():
            self.routing_stats[model_name] = {
                "total_requests": 0,
                "avg_response_time": 0.0,
                "error_count": 0,
                "success_rate": 1.0
            }
    
    async def initialize(self):
        """Initialize LLM router services."""
        try:
            # Start load monitoring
            await self._start_load_monitoring()
            
            # Validate model endpoints
            await self._validate_model_endpoints()
            
            self.running = True
            logger.info("LLM router services started successfully")
            
        except Exception as e:
            logger.error("Failed to initialize LLM router", error=str(e))
            raise
    
    async def _start_load_monitoring(self):
        """Start background load monitoring for all models."""
        asyncio.create_task(self._monitor_model_loads())
        logger.info("Model load monitoring started")
    
    async def _monitor_model_loads(self):
        """Monitor model loads and update availability."""
        while self.running:
            try:
                for model_name, model in self.models.items():
                    # Simulate load monitoring (in production, use actual metrics)
                    current_load = await self._get_model_load(model)
                    model.current_load = current_load
                    
                    # Update availability based on load
                    if current_load > 0.9:
                        model.available = False
                        logger.warning("Model overloaded, marking unavailable", 
                                     model=model_name, load=current_load)
                    elif not model.available and current_load < 0.7:
                        model.available = True
                        logger.info("Model load normalized, marking available", 
                                   model=model_name, load=current_load)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error("Error in load monitoring", error=str(e))
                await asyncio.sleep(5)
    
    async def _get_model_load(self, model: LLMModel) -> float:
        """Get current load for a specific model."""
        try:
            # Simulate load calculation based on recent requests
            import random
            base_load = min(model.current_requests / model.rate_limit, 1.0)
            # Add some random variation to simulate real load
            variation = random.uniform(-0.1, 0.1)
            return max(0.0, min(1.0, base_load + variation))
            
        except Exception as e:
            logger.error("Error getting model load", model=model.name, error=str(e))
            return 0.5  # Default moderate load
    
    async def _validate_model_endpoints(self):
        """Validate that all model endpoints are reachable."""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=5)

            # Check Ollama availability first
            ollama_available = await self.ollama_client.check_health()
            if ollama_available:
                logger.info("Ollama service is available")
                # Get list of available Ollama models
                available_models = await self.ollama_client.list_models()
                available_model_names = [m.get("name", "") for m in available_models]
                logger.info("Available Ollama models", models=available_model_names)
            else:
                logger.warning("Ollama service is not available - local models will be unavailable")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                for model_name, model in self.models.items():
                    try:
                        # Check if this is a local Ollama model
                        if "local" in model_name.lower() or model.endpoint == "localhost:11434":
                            # Check Ollama availability
                            if ollama_available:
                                # Check if specific model is available
                                model_available = any(model.model_id in m for m in available_model_names)
                                if model_available:
                                    model.available = True
                                    logger.info("Local model available", model=model_name)
                                else:
                                    model.available = False
                                    logger.warning("Local model not downloaded",
                                                 model=model_name,
                                                 model_id=model.model_id)
                            else:
                                model.available = False
                                logger.warning("Local model unavailable - Ollama not running",
                                             model=model_name)
                        else:
                            # Remote model - check HTTP endpoint
                            health_url = f"http://{model.endpoint}/health"
                            async with session.get(health_url) as response:
                                if response.status == 200:
                                    logger.info("Model endpoint validated", model=model_name)
                                else:
                                    logger.warning("Model endpoint unhealthy",
                                                 model=model_name, status=response.status)
                                    # Keep model available for demo purposes
                                    # model.available = False
                    except Exception as e:
                        logger.warning("Model endpoint unreachable",
                                     model=model_name, error=str(e))
                        # Keep remote models available for demo purposes even if endpoint is unreachable
                        # For local models, mark as unavailable if check fails
                        if "local" in model_name.lower():
                            model.available = False

        except Exception as e:
            logger.error("Error validating model endpoints", error=str(e))
    
    async def analyze_query(self, query: str, context: Optional[Dict] = None) -> QueryAnalysis:
        """Analyze incoming query to determine routing strategy."""
        try:
            context = context or {}
            
            # Query type classification
            query_type = self._classify_query_type(query)
            
            # Complexity analysis
            complexity_score = self._calculate_complexity_score(query)
            
            # Token estimation
            estimated_tokens = len(query.split()) * 1.3  # Rough estimation
            
            # Priority determination
            priority = self._determine_priority(query, context)
            
            # Feature detection
            requires_reasoning = self._requires_reasoning(query)
            requires_creativity = self._requires_creativity(query)
            
            # Language detection (simplified)
            language = context.get("language", "en")
            
            analysis = QueryAnalysis(
                query_type=query_type,
                complexity_score=complexity_score,
                estimated_tokens=int(estimated_tokens),
                priority=priority,
                requires_reasoning=requires_reasoning,
                requires_creativity=requires_creativity,
                language=language
            )
            
            logger.debug("Query analyzed", 
                        query_type=query_type.value,
                        complexity=complexity_score,
                        tokens=analysis.estimated_tokens)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing query", error=str(e))
            # Return default analysis
            return QueryAnalysis(
                query_type=QueryType.GENERAL,
                complexity_score=0.5,
                estimated_tokens=100,
                priority="medium",
                requires_reasoning=False,
                requires_creativity=False
            )
    
    def _classify_query_type(self, query: str) -> QueryType:
        """Classify query type based on content analysis."""
        query_lower = query.lower()
        
        # Code-related keywords
        code_keywords = ['code', 'function', 'algorithm', 'programming', 'debug', 'implement']
        if any(keyword in query_lower for keyword in code_keywords):
            return QueryType.CODE_GENERATION
        
        # Math keywords
        math_keywords = ['calculate', 'solve', 'equation', 'formula', 'mathematics']
        if any(keyword in query_lower for keyword in math_keywords):
            return QueryType.MATH_COMPUTATION
        
        # Creative keywords
        creative_keywords = ['write', 'story', 'poem', 'creative', 'imagine']
        if any(keyword in query_lower for keyword in creative_keywords):
            return QueryType.CREATIVE_WRITING
        
        # Analysis keywords
        analysis_keywords = ['analyze', 'data', 'statistics', 'trends', 'insights']
        if any(keyword in query_lower for keyword in analysis_keywords):
            return QueryType.DATA_ANALYSIS
        
        # Summarization keywords
        summary_keywords = ['summarize', 'summary', 'key points', 'tldr']
        if any(keyword in query_lower for keyword in summary_keywords):
            return QueryType.SUMMARIZATION
        
        # Translation keywords
        translation_keywords = ['translate', 'translation', 'language']
        if any(keyword in query_lower for keyword in translation_keywords):
            return QueryType.TRANSLATION
        
        # Complex reasoning indicators
        reasoning_keywords = ['explain', 'why', 'how', 'reasoning', 'logic', 'because']
        if any(keyword in query_lower for keyword in reasoning_keywords) and len(query) > 100:
            return QueryType.COMPLEX_REASONING
        
        # Simple Q&A
        if query.endswith('?') and len(query) < 100:
            return QueryType.SIMPLE_QA
        
        return QueryType.GENERAL
    
    def _calculate_complexity_score(self, query: str) -> float:
        """Calculate complexity score (0.0 to 1.0) based on query characteristics."""
        score = 0.0
        
        # Length factor
        length_score = min(len(query) / 500, 1.0)
        score += length_score * 0.3
        
        # Question complexity
        question_words = ['why', 'how', 'explain', 'analyze', 'compare', 'contrast']
        question_count = sum(1 for word in question_words if word in query.lower())
        score += min(question_count / 3, 1.0) * 0.4
        
        # Technical terms
        technical_terms = re.findall(r'\b[A-Z]{2,}\b|\b\w*(?:tion|ment|ness|ity)\b', query)
        tech_score = min(len(technical_terms) / 10, 1.0)
        score += tech_score * 0.2
        
        # Sentence complexity
        sentences = query.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        complexity_score = min(avg_sentence_length / 20, 1.0)
        score += complexity_score * 0.1
        
        return min(score, 1.0)
    
    def _determine_priority(self, query: str, context: Dict) -> str:
        """Determine query priority based on content and context."""
        # Check for priority indicators in context
        if context.get("urgent", False) or context.get("priority", "").lower() == "high":
            return "high"
        
        # Check for priority keywords in query
        priority_keywords = ['urgent', 'immediately', 'asap', 'critical']
        if any(keyword in query.lower() for keyword in priority_keywords):
            return "high"
        
        # Short queries are typically low priority
        if len(query.split()) < 10:
            return "low"
        
        return "medium"
    
    def _requires_reasoning(self, query: str) -> bool:
        """Check if query requires complex reasoning."""
        reasoning_indicators = [
            'why', 'how', 'explain', 'reasoning', 'logic', 'because',
            'analyze', 'compare', 'contrast', 'evaluate', 'justify'
        ]
        return any(indicator in query.lower() for indicator in reasoning_indicators)
    
    def _requires_creativity(self, query: str) -> bool:
        """Check if query requires creative thinking."""
        creative_indicators = [
            'creative', 'imagine', 'invent', 'design', 'brainstorm',
            'write', 'story', 'poem', 'novel', 'original'
        ]
        return any(indicator in query.lower() for indicator in creative_indicators)
    
    async def route_query(self, query: str, context: Optional[Dict] = None) -> RoutingDecision:
        """Route query to the best available LLM model."""
        try:
            # Analyze the query
            analysis = await self.analyze_query(query, context)
            
            # Score all available models
            model_scores = await self._score_models(analysis)
            
            if not model_scores:
                raise ValueError("No available models for routing")
            
            # Select best model
            best_model, best_score = max(model_scores.items(), key=lambda x: x[1]['total_score'])
            
            # Create routing decision
            decision = RoutingDecision(
                selected_model=best_model,
                confidence_score=best_score['total_score'],
                reasoning=best_score['reasoning'],
                alternative_models=[m for m, s in sorted(model_scores.items(), 
                                                        key=lambda x: x[1]['total_score'], 
                                                        reverse=True)[1:3]],
                estimated_cost=best_score['estimated_cost'],
                estimated_response_time=best_score['estimated_response_time'],
                load_factor=self.models[best_model].current_load
            )
            
            # Record routing decision
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            self.query_history.append((query_hash, best_model, time.time()))
            
            # Update model request count
            self.models[best_model].record_request()
            
            logger.info("Query routed to model",
                       model=best_model,
                       query_type=analysis.query_type.value,
                       confidence=decision.confidence_score,
                       load=decision.load_factor)
            
            return decision
            
        except Exception as e:
            logger.error("Error routing query", error=str(e))
            # Fallback to default model
            fallback_model = "gpt-4" if self.models["gpt-4"].available else "claude-3"
            return RoutingDecision(
                selected_model=fallback_model,
                confidence_score=0.5,
                reasoning="Fallback routing due to error",
                alternative_models=[],
                estimated_cost=0.01,
                estimated_response_time=3.0,
                load_factor=self.models[fallback_model].current_load
            )
    
    async def _score_models(self, analysis: QueryAnalysis) -> Dict[str, Dict]:
        """Score all available models for the given query analysis."""
        scores = {}
        
        for model_name, model in self.models.items():
            if not model.available or not model.can_handle_request():
                continue
            
            # Capability score
            capability = model.capabilities.get(analysis.query_type, ModelCapability.FAIR)
            capability_score = {
                ModelCapability.EXCELLENT: 1.0,
                ModelCapability.GOOD: 0.8,
                ModelCapability.FAIR: 0.6,
                ModelCapability.POOR: 0.2
            }[capability]
            
            # Load score (inverse of current load)
            load_score = 1.0 - model.current_load
            
            # Cost score (inverse of cost, normalized)
            max_cost = max(m.cost_per_token for m in self.models.values())
            cost_score = 1.0 - (model.cost_per_token / max_cost) if max_cost > 0 else 1.0
            
            # Response time score (inverse of response time)
            max_response_time = max(m.avg_response_time for m in self.models.values())
            response_time_score = 1.0 - (model.avg_response_time / max_response_time) if max_response_time > 0 else 1.0
            
            # Weighted total score
            total_score = (
                capability_score * self.load_balancing_weights["capability"] +
                load_score * self.load_balancing_weights["load"] +
                cost_score * self.load_balancing_weights["cost"] +
                response_time_score * self.load_balancing_weights["response_time"]
            )
            
            # Adjust for query complexity and priority
            if analysis.is_complex and capability == ModelCapability.EXCELLENT:
                total_score *= 1.2
            
            if analysis.priority == "high":
                total_score *= 1.1
            elif analysis.priority == "low":
                total_score *= 0.9
            
            scores[model_name] = {
                "total_score": total_score,
                "capability_score": capability_score,
                "load_score": load_score,
                "cost_score": cost_score,
                "response_time_score": response_time_score,
                "reasoning": f"Best fit for {analysis.query_type.value} queries with {capability.value} capability",
                "estimated_cost": analysis.estimated_tokens * model.cost_per_token,
                "estimated_response_time": model.avg_response_time * (1 + model.current_load)
            }
        
        return scores
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics and model performance metrics."""
        stats = {
            "total_queries": len(self.query_history),
            "models": {},
            "query_distribution": {},
            "performance_metrics": {}
        }
        
        # Model statistics
        for model_name, model in self.models.items():
            model_queries = sum(1 for _, m, _ in self.query_history if m == model_name)
            
            stats["models"][model_name] = {
                "available": model.available,
                "current_load": model.current_load,
                "current_requests": model.current_requests,
                "rate_limit": model.rate_limit,
                "total_queries_routed": model_queries,
                "avg_response_time": model.avg_response_time,
                "cost_per_token": model.cost_per_token
            }
        
        # Query type distribution
        query_types = [analysis.query_type.value for analysis in []]
        for query_type in QueryType:
            stats["query_distribution"][query_type.value] = query_types.count(query_type.value)
        
        # Performance metrics
        if self.query_history:
            recent_queries = self.query_history[-100:]  # Last 100 queries
            response_times = []
            
            for query_hash, model_name, timestamp in recent_queries:
                model = self.models[model_name]
                response_times.append(model.avg_response_time)
            
            if response_times:
                stats["performance_metrics"] = {
                    "avg_response_time": statistics.mean(response_times),
                    "median_response_time": statistics.median(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times)
                }
        
        return stats
    
    async def cleanup(self):
        """Clean up LLM router resources."""
        self.running = False
        logger.info("LLM router cleaned up")