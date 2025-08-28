"""
Local LLM Integration Client

Client for communicating with local LLM API endpoints for protocol compliance
analysis. Supports OpenAI-compatible API format and provides robust error
handling, retry logic, and response validation.

Features:
- OpenAI-compatible API client
- Configurable model parameters
- Automatic retry with exponential backoff
- Response validation and parsing
- Structured logging and monitoring
- Error handling and fallback options
"""
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import asyncio
from urllib.parse import urljoin

from ...config.settings import settings
from ...utils import logger, LLMError, ProtocolValidationError

@dataclass
class LLMMessage:
    """
    Message in LLM conversation format.
    
    Attributes:
        role: Message role ('system', 'user', 'assistant')
        content: Message content text
        name: Optional name for the message sender
    """
    role: str
    content: str
    name: Optional[str] = None

@dataclass
class LLMRequest:
    """
    Request to LLM API.
    
    Attributes:
        messages: List of conversation messages
        model: Model name to use
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty parameter
        presence_penalty: Presence penalty parameter
        stop: Stop sequences
        stream: Whether to stream response
    """
    messages: List[LLMMessage]
    model: str
    temperature: float = 0.6
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False

@dataclass
class LLMResponse:
    """
    Response from LLM API.
    
    Attributes:
        content: Generated text content
        role: Response role (usually 'assistant')
        model: Model that generated the response
        usage: Token usage statistics
        finish_reason: Reason for completion ('stop', 'length', etc.)
        response_time: Time taken for response in seconds
        raw_response: Raw API response data
    """
    content: str
    role: str = "assistant"
    model: str = ""
    usage: Dict[str, int] = None
    finish_reason: str = ""
    response_time: float = 0.0
    raw_response: Dict[str, Any] = None

class LLMClient:
    """
    Client for local LLM API integration.
    
    Provides a high-level interface for communicating with local LLM
    endpoints using OpenAI-compatible API format. Handles authentication,
    retries, error handling, and response parsing.
    
    Attributes:
        api_url: Base URL for LLM API
        model_name: Default model name
        temperature: Default sampling temperature
        max_tokens: Default maximum tokens
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        system_prompt: Default system prompt
    """
    
    def __init__(self,
                 api_url: str = None,
                 model_name: str = None,
                 temperature: float = None,
                 max_tokens: int = None,
                 timeout: int = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Initialize the LLM client.
        
        Args:
            api_url: LLM API endpoint URL (defaults to config)
            model_name: Model name (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Maximum tokens (defaults to config) 
            timeout: Request timeout (defaults to config)
            max_retries: Maximum retry attempts
            retry_delay: Base retry delay in seconds
        """
        self.api_url = api_url or settings.llm.api_url
        self.model_name = model_name or settings.llm.model_name
        self.temperature = temperature or settings.llm.temperature
        self.max_tokens = max_tokens or settings.llm.max_tokens
        self.timeout = timeout or settings.llm.timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.system_prompt = settings.llm.system_prompt
        
        # Validate API URL
        if not self.api_url:
            raise LLMError("LLM API URL not configured")
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Guardian-Backend/1.0'
        })
        
        logger.info(
            "Initialized LLMClient",
            api_url=self.api_url,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )
    
    def chat_completion(self,
                       messages: List[Union[LLMMessage, Dict[str, str]]],
                       model: str = None,
                       temperature: float = None,
                       max_tokens: int = None,
                       **kwargs) -> LLMResponse:
        """
        Send a chat completion request to the LLM.
        
        Args:
            messages: List of messages in conversation format
            model: Model name (uses default if not provided)
            temperature: Sampling temperature (uses default if not provided)
            max_tokens: Maximum tokens (uses default if not provided)
            **kwargs: Additional parameters for the API
            
        Returns:
            LLMResponse: Response from the LLM
            
        Raises:
            LLMError: If request fails
            LLMError: If network error occurs
            ProtocolValidationError: If request validation fails
        """
        start_time = time.time()
        
        try:
            # Prepare request
            request = self._prepare_request(
                messages, model, temperature, max_tokens, **kwargs
            )
            
            # Send request with retries
            response_data = self._send_request_with_retries(request)
            
            # Parse response
            llm_response = self._parse_response(response_data, time.time() - start_time)
            
            logger.info(
                "LLM chat completion successful",
                model=llm_response.model,
                response_time=llm_response.response_time,
                content_length=len(llm_response.content),
                usage=llm_response.usage
            )
            
            return llm_response
            
        except (LLMError, LLMError, ProtocolValidationError):
            raise
        except Exception as e:
            error_msg = f"LLM chat completion failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise LLMError(error_msg)
    
    def simple_completion(self,
                         prompt: str,
                         system_prompt: str = None,
                         **kwargs) -> str:
        """
        Simple completion with a single prompt.
        
        Args:
            prompt: User prompt text
            system_prompt: System prompt (uses default if not provided)
            **kwargs: Additional parameters for chat completion
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If completion fails
        """
        system_prompt = system_prompt or self.system_prompt
        
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=prompt)
        ]
        
        response = self.chat_completion(messages, **kwargs)
        return response.content
    
    def _prepare_request(self,
                        messages: List[Union[LLMMessage, Dict[str, str]]],
                        model: str,
                        temperature: float,
                        max_tokens: int,
                        **kwargs) -> Dict[str, Any]:
        """
        Prepare the API request payload.
        
        Args:
            messages: Conversation messages
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            Request payload dictionary
            
        Raises:
            ProtocolValidationError: If request validation fails
        """
        # Convert messages to dict format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.name:
                    msg_dict["name"] = msg.name
                formatted_messages.append(msg_dict)
            elif isinstance(msg, dict):
                if "role" not in msg or "content" not in msg:
                    raise ProtocolValidationError("Message must have 'role' and 'content' fields")
                formatted_messages.append(msg)
            else:
                raise ProtocolValidationError(f"Invalid message type: {type(msg)}")
        
        # Validate messages
        if not formatted_messages:
            raise ProtocolValidationError("At least one message is required")
        
        # Build request payload
        payload = {
            "model": model or self.model_name,
            "messages": formatted_messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            **kwargs
        }
        
        # Validate parameters
        if payload["temperature"] < 0 or payload["temperature"] > 1:
            raise ProtocolValidationError("Temperature must be between 0 and 1")
        
        if payload["max_tokens"] < 1:
            raise ProtocolValidationError("max_tokens must be positive")
        
        return payload
    
    def _send_request_with_retries(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request with retry logic.
        
        Args:
            payload: Request payload
            
        Returns:
            Response data dictionary
            
        Raises:
            LLMError: If network request fails
            LLMError: If API returns error
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    self.api_url,
                    data=json.dumps(payload),
                    timeout=self.timeout
                )
                
                # Handle HTTP errors
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit - wait longer before retry
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt) * 2
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMError("Rate limit exceeded, max retries reached")
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise LLMError(f"Server error: {response.status_code}")
                else:
                    # Client error - don't retry
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    except:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                    raise LLMError(f"API error: {error_msg}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Network error, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise LLMError(f"Network request failed: {str(e)}")
        
        # If we get here, all retries failed
        raise LLMError(f"All {self.max_retries + 1} request attempts failed")
    
    def _parse_response(self, response_data: Dict[str, Any], response_time: float) -> LLMResponse:
        """
        Parse the API response.
        
        Args:
            response_data: Raw response data
            response_time: Time taken for response
            
        Returns:
            Parsed LLMResponse object
            
        Raises:
            LLMError: If response parsing fails
        """
        try:
            # Extract the main response content
            choices = response_data.get('choices', [])
            if not choices:
                raise LLMError("No choices in response")
            
            choice = choices[0]
            message = choice.get('message', {})
            
            return LLMResponse(
                content=message.get('content', ''),
                role=message.get('role', 'assistant'),
                model=response_data.get('model', ''),
                usage=response_data.get('usage', {}),
                finish_reason=choice.get('finish_reason', ''),
                response_time=response_time,
                raw_response=response_data
            )
            
        except Exception as e:
            error_msg = f"Failed to parse LLM response: {str(e)}"
            logger.error(error_msg, response_data=response_data, exception=e)
            raise LLMError(error_msg)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the LLM API is available and responding.
        
        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            
            # Simple test request
            test_messages = [
                LLMMessage(role="user", content="Hello")
            ]
            
            response = self.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0.1
            )
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "api_url": self.api_url,
                "model": response.model,
                "response_time": response_time,
                "test_response": response.content[:50] + "..." if len(response.content) > 50 else response.content
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_url": self.api_url,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.debug("Closed LLM client session")

# Global instance for use throughout the application
llm_client = LLMClient()