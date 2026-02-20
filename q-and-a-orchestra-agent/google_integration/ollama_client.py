import logging
import json
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaHybridClient:
    """Client for interacting with Ollama models"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.usage_stats = {
            'requests': 0,
            'tokens_in': 0,
            'tokens_out': 0,
            'errors': 0
        }
    
    async def extract_emails(self, content: str, agent_data: Dict, use_cloud: bool = False) -> Dict:
        """Extract emails using Ollama models"""
        self.usage_stats['requests'] += 1
        
        # Select model
        model = "llama3.3:70b" if use_cloud else "mistral:7b"
        
        prompt = f"""
        Extract email addresses for the following real estate agent.
        Return ONLY a JSON object with keys: 'emails' (list of strings), 'confidence' (0-1 float).
        
        Agent Data: {json.dumps(agent_data)}
        
        Context:
        {content}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    result = await response.json()
                    response_text = result.get('response', '{}')
                    
                    # Track stats (approximate)
                    self.usage_stats['tokens_in'] += len(prompt) // 4
                    self.usage_stats['tokens_out'] += len(response_text) // 4
                    
                    try:
                        parsed = json.loads(response_text)
                        return {
                            'emails': parsed.get('emails', []),
                            'confidence': parsed.get('confidence', 0.0),
                            'method': f'ollama_{model}'
                        }
                    except json.JSONDecodeError:
                        return {
                            'emails': [],
                            'error': 'Failed to parse JSON response',
                            'raw_response': response_text,
                            'method': f'ollama_{model}'
                        }
                        
        except Exception as e:
            self.usage_stats['errors'] += 1
            logger.error(f"Ollama extraction failed: {e}")
            return {
                'emails': [],
                'error': str(e),
                'method': f'ollama_{model}'
            }

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return self.usage_stats.copy()
