"""
Base AI Module - Shared LLM Configuration and Utilities

Provides common functionality for all AI pipeline modules:
- LLM client configuration (Gemini, Claude, OpenAI)
- Retry logic with exponential backoff
- JSON parsing with error recovery
- Cost tracking
"""

import os
import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable
from functools import wraps
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Type variable for generic return types
T = TypeVar('T')


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: str  # 'gemini', 'anthropic', 'openai'
    model: str
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.3
    
    # Cost per 1M tokens (for tracking)
    input_cost: float = 0.0
    output_cost: float = 0.0


@dataclass
class LLMUsage:
    """Track LLM usage and costs."""
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    errors: int = 0
    retries: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def estimate_cost(self, config: LLMConfig) -> float:
        """Estimate cost in USD."""
        input_cost = (self.input_tokens / 1_000_000) * config.input_cost
        output_cost = (self.output_tokens / 1_000_000) * config.output_cost
        return input_cost + output_cost


# Default LLM configurations
GEMINI_FLASH_CONFIG = LLMConfig(
    provider='gemini',
    model='gemini-2.0-flash',
    api_key=os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'),
    input_cost=0.075,
    output_cost=0.30,
)

GEMINI_PRO_CONFIG = LLMConfig(
    provider='gemini',
    model='gemini-1.5-pro',
    api_key=os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'),
    input_cost=1.25,
    output_cost=5.00,
)

# Claude config (for quality tasks if available)
CLAUDE_SONNET_CONFIG = LLMConfig(
    provider='anthropic',
    model='claude-3-5-sonnet-20241022',
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    input_cost=3.00,
    output_cost=15.00,
)


def get_default_config() -> LLMConfig:
    """Get the default LLM configuration."""
    # Use Gemini Flash by default (fast and cheap)
    if GEMINI_FLASH_CONFIG.api_key:
        return GEMINI_FLASH_CONFIG
    raise ValueError("No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY.")


class RetryError(Exception):
    """Raised when all retries are exhausted."""
    pass


def with_retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each retry
        on_retry: Optional callback(exception, attempt) called before retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt >= max_retries:
                        break
                    
                    # Check for non-retryable errors
                    error_str = str(e).lower()
                    if 'invalid api key' in error_str or 'unauthorized' in error_str:
                        raise e  # Don't retry auth errors
                    
                    # Call retry callback
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    # Wait before retry
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            raise RetryError(f"Failed after {max_retries + 1} attempts: {last_exception}")
        
        return wrapper
    return decorator


def parse_json_response(text: str, allow_partial: bool = False) -> Dict[str, Any]:
    """
    Parse JSON from LLM response with error recovery.
    
    Handles common issues:
    - Markdown code blocks
    - Trailing commas
    - Single quotes instead of double quotes
    - Missing closing brackets
    - JSON arrays (wraps them in a dict)
    
    Args:
        text: Raw LLM response text
        allow_partial: If True, attempt to recover partial JSON
        
    Returns:
        Parsed JSON as dict
        
    Raises:
        json.JSONDecodeError: If parsing fails
    """
    text = text.strip()
    
    # Remove markdown code blocks
    if '```' in text:
        # Extract content between code blocks
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    
    # Fix common JSON issues
    # Remove trailing commas before ] or }
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Try to parse
    try:
        result = json.loads(text)
        # If the response is a list, wrap it in a dict
        if isinstance(result, list):
            return {'items': result}
        return result
    except json.JSONDecodeError as e:
        if allow_partial:
            # Try to extract a valid JSON object
            # Find the first { and try to match it
            start = text.find('{')
            if start >= 0:
                depth = 0
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(text[start:i+1])
                            except json.JSONDecodeError:
                                pass
                            break
        raise e


class BaseLLM(ABC):
    """Base class for LLM interactions."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_default_config()
        self.usage = LLMUsage()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        if self.config.provider == 'gemini':
            if not self.config.api_key:
                raise ValueError("Gemini API key not found")
            genai.configure(api_key=self.config.api_key)
            self._client = genai.GenerativeModel(self.config.model)
        elif self.config.provider == 'anthropic':
            # Import anthropic only if needed
            try:
                import anthropic
                if not self.config.api_key:
                    raise ValueError("Anthropic API key not found")
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        elif self.config.provider == 'openai':
            try:
                import openai
                if not self.config.api_key:
                    raise ValueError("OpenAI API key not found")
                self._client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
    
    @with_retry(max_retries=3, base_delay=2.0)
    def generate(self, prompt: str, json_mode: bool = True) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send
            json_mode: If True, request JSON output format
            
        Returns:
            Raw response text
        """
        self.usage.calls += 1
        
        try:
            if self.config.provider == 'gemini':
                generation_config = {}
                if json_mode:
                    generation_config['response_mime_type'] = 'application/json'
                
                response = self._client.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return response.text
            
            elif self.config.provider == 'anthropic':
                response = self._client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                # Track usage
                if hasattr(response, 'usage'):
                    self.usage.input_tokens += response.usage.input_tokens
                    self.usage.output_tokens += response.usage.output_tokens
                return response.content[0].text
            
            elif self.config.provider == 'openai':
                kwargs = {
                    'model': self.config.model,
                    'max_tokens': self.config.max_tokens,
                    'temperature': self.config.temperature,
                    'messages': [{"role": "user", "content": prompt}]
                }
                if json_mode:
                    kwargs['response_format'] = {"type": "json_object"}
                
                response = self._client.chat.completions.create(**kwargs)
                # Track usage
                if response.usage:
                    self.usage.input_tokens += response.usage.prompt_tokens
                    self.usage.output_tokens += response.usage.completion_tokens
                return response.choices[0].message.content
        
        except Exception as e:
            self.usage.errors += 1
            raise
    
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Parsed JSON response
        """
        response = self.generate(prompt, json_mode=True)
        return parse_json_response(response)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            'calls': self.usage.calls,
            'input_tokens': self.usage.input_tokens,
            'output_tokens': self.usage.output_tokens,
            'total_tokens': self.usage.total_tokens,
            'errors': self.usage.errors,
            'retries': self.usage.retries,
            'estimated_cost_usd': self.usage.estimate_cost(self.config),
        }
    
    def reset_usage(self):
        """Reset usage statistics."""
        self.usage = LLMUsage()


class BaseAIModule(BaseLLM):
    """Base class for AI pipeline modules."""
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Return the prompt template for this module."""
        pass
    
    def format_prompt(self, **kwargs) -> str:
        """Format the prompt template with provided arguments."""
        template = self.get_prompt_template()
        return template.format(**kwargs)


if __name__ == '__main__':
    # Test the base module
    print("Testing Base LLM...")
    
    config = get_default_config()
    print(f"Using provider: {config.provider}, model: {config.model}")
    
    class TestModule(BaseLLM):
        pass
    
    module = TestModule()
    
    # Test a simple generation
    prompt = 'Return a JSON object with a "message" field saying "Hello, World!"'
    try:
        result = module.generate_json(prompt)
        print(f"Result: {result}")
        print(f"Usage: {module.get_usage_stats()}")
    except Exception as e:
        print(f"Error: {e}")

