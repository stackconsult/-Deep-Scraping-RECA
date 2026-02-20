from typing import Dict
from .schemas import ContactInfo

class DataValidator:
    """Validates extracted data"""
    
    async def validate(self, contact_info: ContactInfo, agent_data: Dict) -> ContactInfo:
        """Validate and clean contact information"""
        
        # Verify email domain matches brokerage if possible
        if contact_info.email:
            brokerage_domain = self._extract_brokerage_domain(agent_data.get('brokerage', ''))
            if brokerage_domain and brokerage_domain in contact_info.email:
                contact_info.email_verified = True
        
        # Ensure data consistency
        if not contact_info.email and not contact_info.phone:
            # If no direct contact info, mark as low confidence result implicitly
            pass
            
        return contact_info
    
    def _extract_brokerage_domain(self, brokerage: str) -> str:
        """Extract domain from brokerage name"""
        # Simplistic extraction for validation hint
        if not brokerage:
            return ""
        
        clean = brokerage.lower()
        clean = clean.replace(' ', '').replace('.', '').replace('/', '')
        return clean
