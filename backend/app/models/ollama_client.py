#!/usr/bin/env python3
"""
Ollama Client for Local LLM Integration
Provides interface to locally running Ollama models.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models in Ollama.
        
        Returns:
            List of model information dictionaries
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    else:
                        logger.error("Failed to list Ollama models", status=response.status)
                        return []
        except Exception as e:
            logger.error("Error listing Ollama models", error=str(e))
            return []
    
    async def generate(self, model: str, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate completion from Ollama model.
        
        Args:
            model: Model name (e.g., "llama3.2:3b")
            prompt: Input prompt
            stream: Whether to stream the response
            
        Returns:
            Response dictionary with generated text
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        if stream:
                            # Handle streaming response
                            full_response = ""
                            async for line in response.content:
                                if line:
                                    try:
                                        chunk = json.loads(line.decode('utf-8'))
                                        full_response += chunk.get("response", "")
                                        if chunk.get("done", False):
                                            return {
                                                "response": full_response,
                                                "model": model,
                                                "done": True
                                            }
                                    except json.JSONDecodeError:
                                        continue
                            return {"response": full_response, "model": model, "done": True}
                        else:
                            # Non-streaming response
                            data = await response.json()
                            return data
                    else:
                        logger.error("Ollama generation failed", status=response.status, model=model)
                        return {"error": f"HTTP {response.status}", "response": ""}
        except asyncio.TimeoutError:
            logger.error("Ollama generation timeout", model=model)
            return {"error": "Timeout", "response": ""}
        except Exception as e:
            logger.error("Error generating with Ollama", error=str(e), model=model)
            return {"error": str(e), "response": ""}
    
    async def check_health(self) -> bool:
        """Check if Ollama service is running and healthy.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/tags", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug("Ollama health check failed", error=str(e))
            return False
    
    async def pull_model(self, model: str) -> bool:
        """Pull/download a model from Ollama registry.
        
        Args:
            model: Model name to pull (e.g., "llama3.2:3b")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {"name": model}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/pull",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 minutes for download
                ) as response:
                    if response.status == 200:
                        logger.info("Model pulled successfully", model=model)
                        return True
                    else:
                        logger.error("Failed to pull model", status=response.status, model=model)
                        return False
        except Exception as e:
            logger.error("Error pulling model", error=str(e), model=model)
            return False


# Global Ollama client instance
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client instance.

    Returns:
        OllamaClient instance
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
