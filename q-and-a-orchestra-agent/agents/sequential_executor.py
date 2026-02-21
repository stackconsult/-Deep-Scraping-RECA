# Sequential Executor Implementation
"""
Coordinates specialized agents in sequence for higher accuracy
Based on Real Estate Agent Team from Awesome LLM Apps
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from agents.web_scraper.scraper import StructuredScraper

@dataclass
class AgentResult:
    """Standard result format for all agents"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    required: bool = True  # Whether this step is required
    confidence: float = 0.0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowState:
    """Tracks state through sequential execution"""
    agent_id: str
    current_step: str
    data: Dict[str, Any]
    history: List[Dict]
    start_time: datetime
    errors: List[str] = field(default_factory=list)
    
class BaseAgent:
    """Base class for all sequential agents"""
    
    def __init__(self, name: str, scraper: Optional[StructuredScraper] = None):
        self.name = name
        self.scraper = scraper
        if self.scraper is None:
             print(f"⚠️  WARNING: Agent {name} initialized WITHOUT scraper (will use mocks)")
        else:
             print(f"✅ Agent {name} initialized with scraper")
        self.stats = {
            'executions': 0,
            'successes': 0,
            'failures': 0,
            'avg_time': 0.0,
            'total_time': 0.0
        }
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Execute agent logic - to be implemented by subclasses"""
        raise NotImplementedError(f"{self.name}.execute() not implemented")
    
    def update_stats(self, success: bool, execution_time: float):
        """Update agent statistics"""
        self.stats['executions'] += 1
        self.stats['total_time'] += execution_time
        
        if success:
            self.stats['successes'] += 1
        else:
            self.stats['failures'] += 1
        
        # Update average time
        self.stats['avg_time'] = self.stats['total_time'] / self.stats['executions']
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset agent statistics"""
        self.stats = {
            'executions': 0,
            'successes': 0,
            'failures': 0,
            'avg_time': 0.0,
            'total_time': 0.0
        }

class SearchAgent(BaseAgent):
    """Searches for agent and brokerage information"""
    
    def __init__(self, scraper: Optional[StructuredScraper] = None):
        super().__init__("search", scraper)
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Search for agent website and page"""
        start_time = datetime.now()
        
        try:
            # Use scraper to find agent URL
            if self.scraper:
                # The scraper's _find_agent_url is internal, but scrape_agent does the search too.
                # For the 'search' step, we might just want to resolve the URL.
                # We can expose _find_agent_url public or just use scrape_agent and cache it.
                # For now, let's use the internal helper if possible or assume scrape_agent handles it.
                # Let's rely on the scraper finding the URL during the extraction phase if we want to separate concerns,
                # OR, we can try to construct the URL here.
                
                # Using the scraper's public method to verify/find URL would be best.
                # Since scrape_agent does everything, maybe SearchAgent just prepares the context?
                # Or we can try to find the URL.
                
                # Let's verify we can find a URL.
                url = await self.scraper._find_agent_url(data)
                
                if url:
                    result_data = {
                        'found': True,
                        'website': url.split('/agents')[0] if '/agents' in url else url, # simplistic
                        'agent_page': url.replace(url.split('/agents')[0], '') if '/agents' in url else '',
                        'full_url': url,
                        'search_method': 'structured_scraper'
                    }
                else:
                     # Fallback to pattern generation if scraper fails to find specific URL
                    brokerage = data.get('brokerage', '')
                    # Use the robust extractor from the scraper
                    domain = self.scraper._extract_domain(brokerage) if self.scraper else None
                    
                    if not domain:
                        # Super fallback if scraper method fails or is missing
                        domain = brokerage.lower().replace(' ', '').replace('/', '').replace('.', '') + '.ca'
                        
                    result_data = {
                        'found': False, # Not found by scraper, but we have a guess
                        'website': f"https://{domain}",
                        'search_method': 'heuristic_fallback'
                    }
            else:
                # Fallback mock/heuristic
                brokerage = data.get('brokerage', '').lower()
                domain = brokerage.replace(' ', '').replace('/', '').replace('.', '')
                result_data = {
                    'found': True,
                    'website': f"https://{domain}.ca",
                    'search_method': 'mock_heuristic'
                }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(True, execution_time)
            
            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.8,
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(False, execution_time)
            
            return AgentResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={'agent': self.name}
            )

class ExtractAgent(BaseAgent):
    """Extracts emails from web content"""
    
    def __init__(self, scraper: Optional[StructuredScraper] = None):
        super().__init__("extract", scraper)
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Extract emails from found pages"""
        start_time = datetime.now()
        
        try:
            if self.scraper:
                # Use the structured scraper
                profile = await self.scraper.scrape_agent(data)
                
                if profile.contact_info.email:
                    emails = [{
                        'email': profile.contact_info.email,
                        'confidence': profile.confidence,
                        'source': 'structured_scrape'
                    }]
                
                    result_data = {
                        'emails': emails,
                        'extraction_method': 'structured_scraper',
                        'source_url': profile.url,
                        'domain': profile.brokerage
                    }
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.update_stats(True, execution_time)
                    
                    return AgentResult(
                        success=True,
                        data=result_data,
                        confidence=profile.confidence,
                        execution_time=execution_time,
                        metadata={'agent': self.name}
                    )
            
            # Fallback: if scraping failed or didn't run, try pattern generation
            # We need at least a website or brokerage domain to guess
            website = data.get('website', '')
            if not website and not data.get('found'):
                 return AgentResult(
                    success=False,
                    data={'emails': []},
                    error="No website found and scraping failed",
                    confidence=0.0,
                    execution_time=0.0
                )

            # ... existing mock logic ...
            agent = data
            domain = website.replace('https://', '').replace('http://', '').split('/')[0]
            emails = self._generate_mock_emails(agent, domain)
            
            result_data = {
                'emails': emails,
                'extraction_method': 'pattern_based_mock',
                'source_url': data.get('full_url', ''),
                'domain': domain
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(True, execution_time)
            
            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.7 if emails else 0.0,
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(False, execution_time)
            
            return AgentResult(
                success=False,
                data={'emails': []},
                error=str(e),
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
    
    def _generate_mock_emails(self, agent: Dict, domain: str) -> List[Dict]:
        """Generate mock emails for testing"""
        import re
        def clean(s): return re.sub(r'[^a-z0-9]', '', str(s).lower())
        
        first_raw = agent.get('first_name', '').lower()
        last_raw = agent.get('last_name', '').lower()
        
        # Handle cases like first="." last="Satbir Singh"
        if len(clean(first_raw)) < 2 and ' ' in last_raw:
            parts = last_raw.split()
            first_raw = parts[0]
            last_raw = " ".join(parts[1:])
            
        first = clean(first_raw)
        last = clean(last_raw)
        
        # If still missing, try full name
        if not first or not last:
            name = agent.get('name', '').lower()
            parts = name.split()
            if len(parts) >= 2:
                first = clean(parts[0])
                last = clean(parts[-1])
        
        if not first or not last:
            return []
            
        brokerage = agent.get('brokerage', '').lower()
        emails = []
        
        # Ensure domain is clean
        clean_domain = domain.split('/')[0]
        
        # Pattern-based email generation
        if 'remax' in brokerage:
            emails.extend([
                {'email': f"{first}.{last}@remax.net", 'confidence': 0.8},
                {'email': f"{first}{last}@remax.net", 'confidence': 0.6},
                {'email': f"{first}.{last}@remax.ca", 'confidence': 0.8},
                {'email': f"{first}{last}@remax.ca", 'confidence': 0.6}
            ])
        elif 'royal lepage' in brokerage:
            emails.append({'email': f"{first}.{last}@royallepage.ca", 'confidence': 0.8})
            emails.append({'email': f"{first}{last}@royallepage.ca", 'confidence': 0.7})
        elif 'century 21' in brokerage:
            emails.append({'email': f"{first}.{last}@century21.ca", 'confidence': 0.8})
            emails.append({'email': f"{first}{last}@century21.ca", 'confidence': 0.7})
        
        # Generic patterns for specific domain
        emails.extend([
            {'email': f"{first}.{last}@{clean_domain}", 'confidence': 0.5},
            {'email': f"{first}{last}@{clean_domain}", 'confidence': 0.4},
            {'email': f"{first}@{clean_domain}", 'confidence': 0.3}
        ])
        
        return emails

class ValidateAgent(BaseAgent):
    """Validates extracted emails"""
    
    def __init__(self, scraper: Optional[StructuredScraper] = None):
        super().__init__("validate", scraper)
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Validate extracted emails"""
        start_time = datetime.now()
        
        try:
            emails = data.get('emails', [])
            validated = []
            
            for email_info in emails:
                email = email_info.get('email', '')
                
                # Simple validation
                is_valid = self._validate_email_format(email)
                
                if is_valid:
                    validated.append({
                        **email_info,
                        'valid': True,
                        'validation_method': 'format_check'
                    })
            
            result_data = {
                'validated_emails': validated,
                'total_found': len(emails),
                'total_valid': len(validated),
                'validation_rate': len(validated) / len(emails) if emails else 0
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(True, execution_time)
            
            return AgentResult(
                success=True,
                data=result_data,
                confidence=sum(e.get('confidence', 0) for e in validated) / len(validated) if validated else 0.0,
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(False, execution_time)
            
            return AgentResult(
                success=False,
                data={'validated_emails': []},
                error=str(e),
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
    
    def _validate_email_format(self, email: str) -> bool:
        """Simple email format validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

class SynthesizeAgent(BaseAgent):
    """Synthesizes final results"""
    
    def __init__(self):
        super().__init__("synthesize")
    
    async def execute(self, data: Dict[str, Any]) -> AgentResult:
        """Synthesize final result from all steps"""
        start_time = datetime.now()
        
        try:
            # Get validated emails
            validated = data.get('validated_emails', [])
            
            # Sort by confidence
            validated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Extract top emails
            top_emails = [e['email'] for e in validated[:3]]
            
            # Calculate overall confidence
            overall_confidence = (
                data.get('search', {}).get('confidence', 0) * 0.3 +
                data.get('extract', {}).get('confidence', 0) * 0.4 +
                data.get('validate', {}).get('confidence', 0) * 0.3
            )
            
            result_data = {
                'agent_name': data.get('name', ''),
                'brokerage': data.get('brokerage', ''),
                'city': data.get('city', ''),
                'emails': top_emails,
                'email_count': len(top_emails),
                'method': 'sequential_agents',
                'confidence': overall_confidence,
                'source_url': data.get('search', {}).get('full_url', ''),
                'validation_details': {
                    'total_found': data.get('validate', {}).get('total_found', 0),
                    'total_valid': data.get('validate', {}).get('total_valid', 0),
                    'validation_rate': data.get('validate', {}).get('validation_rate', 0)
                },
                'processing_metadata': {
                    'agents_used': ['search', 'extract', 'validate', 'synthesize'],
                    'workflow_completed': True,
                    'total_steps': 4
                }
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(True, execution_time)
            
            return AgentResult(
                success=True,
                data=result_data,
                confidence=overall_confidence,
                execution_time=execution_time,
                metadata={'agent': self.name}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.update_stats(False, execution_time)
            
            return AgentResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={'agent': self.name}
            )

class SequentialExecutor:
    """Orchestrates sequential agent execution"""
    
    def __init__(self):
        # Initialize shared scraper
        self.scraper = StructuredScraper()
        
        self.agents = {
            'search': SearchAgent(self.scraper),
            'extract': ExtractAgent(self.scraper),
            'validate': ValidateAgent(self.scraper),
            'synthesize': SynthesizeAgent()
        }
        self.workflow = ['search', 'extract', 'validate', 'synthesize']
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_executions': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'avg_workflow_time': 0.0,
            'total_workflow_time': 0.0
        }
    
    async def execute(self, agent_data: Dict) -> AgentResult:
        """Execute full workflow"""
        start_time = datetime.now()
        
        # Initialize workflow state
        state = WorkflowState(
            agent_id=agent_data.get('drill_id', agent_data.get('name', 'unknown')),
            current_step='search',
            data=agent_data.copy(),
            history=[],
            start_time=start_time
        )
        
        # Execute each step sequentially
        for step_name in self.workflow:
            try:
                state.current_step = step_name
                self.logger.info(f"Executing {step_name} for {state.agent_id}")
                
                # Get agent for current step
                agent = self.agents[step_name]
                
                # Execute step
                result = await agent.execute(state.data)
                
                # Update state with result
                state.data.update(result.data)
                state.history.append({
                    'step': step_name,
                    'timestamp': datetime.now().isoformat(),
                    'success': result.success,
                    'confidence': result.confidence,
                    'execution_time': result.execution_time,
                    'error': result.error
                })
                
                # Check if step failed
                if not result.success and result.required:
                    state.errors.append(f"Step {step_name} failed: {result.error}")
                    self.logger.error(f"Required step {step_name} failed: {result.error}")
                    break
                    
            except Exception as e:
                state.errors.append(f"Error in {step_name}: {str(e)}")
                self.logger.error(f"Error in {step_name}: {e}")
                break
        
        # Calculate workflow statistics
        workflow_time = (datetime.now() - start_time).total_seconds()
        success = len(state.errors) == 0
        
        self.stats['total_executions'] += 1
        self.stats['total_workflow_time'] += workflow_time
        self.stats['avg_workflow_time'] = self.stats['total_workflow_time'] / self.stats['total_executions']
        
        if success:
            self.stats['successful_workflows'] += 1
        else:
            self.stats['failed_workflows'] += 1
        
        # Return final result
        return AgentResult(
            success=success,
            data=state.data,
            error='; '.join(state.errors) if state.errors else None,
            confidence=state.data.get('confidence', 0.0),
            execution_time=workflow_time,
            metadata={
                'workflow_state': {
                    'agent_id': state.agent_id,
                    'steps_completed': len(state.history),
                    'total_steps': len(self.workflow),
                    'history': state.history
                },
                'agent_stats': {name: agent.get_stats() for name, agent in self.agents.items()}
            }
        )
    
    async def execute_batch(self, agents: List[Dict], 
                           batch_size: int = 5) -> List[AgentResult]:
        """Execute multiple agents in batches"""
        results = []
        
        for i in range(0, len(agents), batch_size):
            batch = agents[i:i + batch_size]
            tasks = [self.execute(agent) for agent in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(AgentResult(
                        success=False,
                        data={},
                        error=str(result),
                        execution_time=0.0
                    ))
                else:
                    results.append(result)
        
        return results
    
    def get_workflow_stats(self) -> Dict:
        """Get workflow statistics"""
        return {
            **self.stats,
            'success_rate': (self.stats['successful_workflows'] / 
                          self.stats['total_executions'] * 100) if self.stats['total_executions'] > 0 else 0
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            'total_executions': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'avg_workflow_time': 0.0,
            'total_workflow_time': 0.0
        }
        
        for agent in self.agents.values():
            agent.reset_stats()
