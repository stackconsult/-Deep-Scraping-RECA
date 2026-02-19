# providers/google_client.py
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from .base_client import BaseModelClient

logger = logging.getLogger(__name__)

class GoogleClient(BaseModelClient):
    """Client for Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.warning("Google API key not provided, client will not work")
        else:
            genai.configure(api_key=self.api_key)
            
    async def invoke(
        self,
        model_id: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Invoke a Google Gemini model."""
        try:
            # Extract system instruction
            system_instruction = None
            gemini_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_messages.append({"role": "model", "parts": [msg["content"]]})

            # Create model
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=system_instruction
            )
            
            # Prepare config
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.7),
                response_mime_type="application/json" if kwargs.get("response_format") == "json_object" else "text/plain"
            )

            # Invoke
            # Note: start_chat / send_message is often easier for multi-turn, 
            # but generate_content with a list of messages works too.
            # For extraction, we often just need one shot or simple chat.
            
            if len(gemini_messages) == 1 and gemini_messages[0]["role"] == "user":
                # Single user message
                response = await asyncio.to_thread(
                    model.generate_content,
                    gemini_messages[0]["parts"][0],
                    generation_config=generation_config
                )
            else:
                # Multi-turn chat
                chat = model.start_chat(history=gemini_messages[:-1])
                response = await asyncio.to_thread(
                    chat.send_message,
                    gemini_messages[-1]["parts"][0],
                    generation_config=generation_config
                )

            # Extract content
            content = response.text
            
            # TODO: Handle tool calls if needed in the future
            tool_calls = []
            
            return {
                "content": content,
                "tool_calls": tool_calls,
                "model": model_id,
                "provider": "google",
                "usage": {
                    # Gemini API usage metadata is available in response.usage_metadata
                    "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                },
                "raw_response": str(response)
            }
            
        except Exception as e:
            logger.error(f"Error invoking Google model {model_id}: {e}")
            raise

    async def get_available_models(self) -> List[str]:
        """Get list of available Gemini models."""
        try:
            models = await asyncio.to_thread(genai.list_models)
            return [m.name for m in models if "generateContent" in m.supported_generation_methods]
        except Exception as e:
            logger.warning(f"Error fetching Google models: {e}")
            return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    def health_check(self) -> bool:
        """Check if Google API is accessible."""
        return bool(self.api_key)
