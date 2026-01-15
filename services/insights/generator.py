"""Insight generator using LLM for business intelligence interpretation."""
import json
import logging
from typing import Dict, Any, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider:
    """Abstract interface for LLM providers."""
    
    def __init__(self, model: str, temperature: float = 0.1, max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(self, prompt: str) -> tuple[str, Dict[str, Any]]:
        """
        Generate completion from prompt.
        
        Returns:
            Tuple of (response_text, metadata)
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(model, **kwargs)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            logger.info(f"Initialized OpenAI provider with model {model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def generate(self, prompt: str) -> tuple[str, Dict[str, Any]]:
        """Generate completion using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst assistant that provides insights based on provided metrics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            metadata = {
                "provider": "openai",
                "model": self.model,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            
            logger.info(f"Generated insights using OpenAI ({metadata['tokens_used']} tokens)")
            return content, metadata
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", **kwargs):
        super().__init__(model, **kwargs)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            logger.info(f"Initialized Anthropic provider with model {model}")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def generate(self, prompt: str) -> tuple[str, Dict[str, Any]]:
        """Generate completion using Anthropic."""
        try:
            # Add JSON formatting instruction
            formatted_prompt = prompt + "\n\nRespond with valid JSON only."
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ]
            )
            
            content = response.content[0].text
            metadata = {
                "provider": "anthropic",
                "model": self.model,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            }
            
            logger.info(f"Generated insights using Anthropic ({metadata['tokens_used']} tokens)")
            return content, metadata
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise


class InsightGenerator:
    """
    Generates business insights from validated metrics using LLM.
    
    Key responsibilities:
    - Accept ONLY validated metrics JSON (never raw data)
    - Use MCP context to constrain LLM behavior
    - Generate executive summary, insights, risks, and recommendations
    - Track LLM usage for audit
    """
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize insight generator.
        
        Args:
            llm_provider: Pre-configured LLM provider instance
            provider_name: Name of provider ("openai" or "anthropic")
            api_key: API key for the provider
            model: Model name to use
        """
        if llm_provider:
            self.llm_provider = llm_provider
        else:
            # Auto-configure from environment or parameters
            provider_name = provider_name or os.getenv("LLM_PROVIDER", "openai")
            api_key = api_key or self._get_api_key(provider_name)
            model = model or self._get_default_model(provider_name)
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
            max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
            
            if provider_name == "openai":
                self.llm_provider = OpenAIProvider(
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider_name == "anthropic":
                self.llm_provider = AnthropicProvider(
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {provider_name}")
        
        logger.info("InsightGenerator initialized")
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key from environment."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        env_var = key_map.get(provider)
        api_key = os.getenv(env_var)
        
        if not api_key:
            raise ValueError(f"API key not found. Set {env_var} environment variable.")
        
        return api_key
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-opus-20240229"
        }
        
        model_env = os.getenv("LLM_MODEL")
        if model_env:
            return model_env
        
        return defaults.get(provider, defaults["openai"])
    
    def generate_insights(
        self,
        metrics: Dict[str, Any],
        business_context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate business insights from metrics.
        
        Args:
            metrics: Validated metrics from EDA service (NO RAW DATA)
            business_context: Optional business context
            
        Returns:
            Dict containing insights, metadata, and LLM tracking info
        """
        logger.info("Starting insight generation")
        
        # Validate that metrics don't contain raw data
        self._validate_no_raw_data(metrics)
        
        # Build MCP context
        from schemas.mcp import build_mcp_context, format_mcp_prompt
        
        mcp_context = build_mcp_context(metrics, business_context)
        prompt = format_mcp_prompt(mcp_context)
        
        # Generate insights using LLM
        start_time = datetime.utcnow()
        response_text, llm_metadata = self.llm_provider.generate(prompt)
        execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Parse response
        try:
            insights = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group())
            else:
                raise ValueError("LLM response is not valid JSON")
        
        # Add metadata
        result = {
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
            "execution_time_ms": execution_time_ms,
            "llm_metadata": llm_metadata,
            "prompt_length": len(prompt),
            "mcp_constraints_applied": True
        }
        
        logger.info(f"Insight generation completed in {execution_time_ms:.2f}ms")
        
        return result
    
    def _validate_no_raw_data(self, metrics: Dict[str, Any]):
        """
        Validate that metrics don't contain raw data.
        
        Raises ValueError if raw data detected.
        """
        # Check for suspicious keys that might indicate raw data
        forbidden_keys = ['raw_data', 'dataframe', 'records', 'rows', 'data']
        
        def check_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check for forbidden keys
                if key.lower() in forbidden_keys:
                    raise ValueError(f"Raw data detected at {current_path}")
                
                # Check for lists that might be record sets
                if isinstance(value, list) and len(value) > 100:
                    # Large lists might be raw records
                    if value and isinstance(value[0], dict):
                        # List of dicts might be records
                        logger.warning(f"Large list of dicts at {current_path} ({len(value)} items)")
                
                # Recursively check nested dicts
                if isinstance(value, dict):
                    check_dict(value, current_path)
        
        check_dict(metrics)
        logger.debug("Validated: No raw data in metrics")
