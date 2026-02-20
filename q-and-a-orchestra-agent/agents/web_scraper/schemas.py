from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

@dataclass
class ContactInfo:
    """Structured contact information"""
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    social_links: Dict[str, str] = field(default_factory=dict)
    additional_contacts: Dict[str, str] = field(default_factory=dict)
    email_verified: bool = False

@dataclass
class AgentProfile:
    """Complete scraped agent profile"""
    found: bool
    agent_name: str = ""
    brokerage: str = ""
    url: str = ""
    contact_info: ContactInfo = field(default_factory=ContactInfo)
    scraped_at: Optional[datetime] = None
    confidence: float = 0.0
    error: Optional[str] = None
