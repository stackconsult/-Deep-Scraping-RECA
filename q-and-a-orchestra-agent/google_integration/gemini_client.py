import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

class GeminiHybridClient:
    """Client for interacting with Google Gemini models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found. Gemini features will be disabled.")
            self.enabled = False
        else:
            genai.configure(api_key=self.api_key)
            self.enabled = True
            
        self.usage_stats = {
            'requests': 0,
            'tokens_in': 0,
            'tokens_out': 0,
            'errors': 0,
            'cost_estimated': 0.0
        }
        
        # Pricing (approximate, per 1M tokens)
        self.pricing = {
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
            'gemini-1.5-pro': {'input': 3.50, 'output': 10.50},
            'gemini-2.0-flash': {'input': 0.10, 'output': 0.40} # Placeholder
        }
    
    async def extract_emails(self, content: str, agent_data: Dict, model: str = "gemini-1.5-flash") -> Dict:
        """Extract emails using Gemini models"""
        if not self.enabled:
            return {'emails': [], 'error': 'Gemini API not enabled', 'method': 'gemini_disabled'}
            
        self.usage_stats['requests'] += 1
        
        prompt = f"""
        Extract email addresses for the following real estate agent.
        Return ONLY a JSON object with keys: 'emails' (list of strings), 'confidence' (0-1 float).
        
        Agent Data: {json.dumps(agent_data)}
        
        Context:
        {content}
        """
        
        try:
            # Configure model
            gen_model = genai.GenerativeModel(model)
            
            # Configure generation
            config = GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
            
            # Run in thread executor to avoid blocking
            response = await asyncio.to_thread(
                gen_model.generate_content,
                prompt,
                generation_config=config
            )
            
            response_text = response.text
            
            # Calculate stats
            if hasattr(response, 'usage_metadata'):
                input_tok = response.usage_metadata.prompt_token_count
                output_tok = response.usage_metadata.candidates_token_count
                self.usage_stats['tokens_in'] += input_tok
                self.usage_stats['tokens_out'] += output_tok
                
                # Estimate cost
                price = self.pricing.get(model, self.pricing['gemini-1.5-flash'])
                cost = (input_tok / 1_000_000 * price['input']) + (output_tok / 1_000_000 * price['output'])
                self.usage_stats['cost_estimated'] += cost
            
            try:
                parsed = json.loads(response_text)
                return {
                    'emails': parsed.get('emails', []),
                    'confidence': parsed.get('confidence', 0.0),
                    'method': f'gemini_{model}'
                }
            except json.JSONDecodeError:
                return {
                    'emails': [],
                    'error': 'Failed to parse JSON response',
                    'raw_response': response_text,
                    'method': f'gemini_{model}'
                }
                
        except Exception as e:
            self.usage_stats['errors'] += 1
            logger.error(f"Gemini extraction failed: {e}")
            return {
                'emails': [],
                'error': str(e),
                'method': f'gemini_{model}'
            }

    async def deep_research(self, query: str, agent_data: Dict) -> Dict:
        """Perform deep research for hard-to-find emails (Simulated Agent)"""
        # In a real implementation with the Deep Research Agent API (once fully public/integrated),
        # this would call the specific agent endpoint. For now, we simulate using Gemini 1.5 Pro
        # with a complex reasoning prompt.
        
        return await self.extract_emails(
            content=f"Perform deep research on: {query}", 
            agent_data=agent_data, 
            model="gemini-1.5-pro"
        )

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return self.usage_stats.copy()
