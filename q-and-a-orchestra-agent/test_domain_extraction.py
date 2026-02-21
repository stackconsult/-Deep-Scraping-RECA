
from typing import Optional

def extract_domain(brokerage: str) -> Optional[str]:
    """Extract domain from brokerage name"""
    if not brokerage:
        return None
        
    clean = brokerage.lower()
    
    # Handle "O/A" (Operating As) - prioritize the brand name
    if ' o/a ' in clean:
        clean = clean.split(' o/a ')[1]
    elif ' o/a' in clean:
        clean = clean.split(' o/a')[1]
        
    # Replace & with 'and' before removing special chars
    clean = clean.replace('&', 'and')
    
    # Remove strict legal suffixes only
    replacements = [
        ' inc.', ' inc', ' ltd.', ' ltd', ' corp.', ' corp', 
        ' corporation', ' limited', ' llc', ' ulc', ' llp'
    ]
    
    for r in replacements:
        if clean.endswith(r):
            clean = clean[:-len(r)]
        elif r in clean:
            clean = clean.replace(r, '')
            
    # Handle special big brands (manual overrides for cleaner domains)
    if 'century 21' in clean:
        return 'century21.ca'
    if 're/max' in clean or 'remax' in clean:
        return 'remax.ca'
    if 'royal lepage' in clean:
        return 'royallepage.ca'
    if 'sothebys' in clean or "sotheby's" in clean:
        return 'sothebysrealty.ca'
    if 'exp realty' in clean:
        return 'exprealty.ca'
        
    # Remove special chars and spaces
    clean = clean.replace('.', '').replace(',', '').replace("'", "").replace('/', '').replace(' ', '')
    
    return f"{clean}.ca"

test_cases = [
    "Max Wright Real Estate Corporation O/A Sotheby's International Realty Canada",
    "Real Estate Professionals Inc.",
    "LPT Realty ULC O/A LPT Realty",
    "RE/MAX Real Estate (Edmonton) Ltd. O/A RE/MAX Real Estate",
    "EXP Realty of Canada Inc. O/A EXP Realty",
    "The Realty Bureau Ltd. o/a The Realty Bureau",
    "Revolution Property Management Inc o/a Revolution Property Management and Real Estate",
    "HR3 Alberta Inc. o/a RE/MAX CROWN",
    "Dynafour Real Estate Limited O/A Cushman & Wakefield Edmonton",
    "Century 21 Foothills South Ltd. o/a Century 21 Foothills South Real Estate"
]

print("New Logic Results:")
for brokerage in test_cases:
    print(f"'{brokerage}' -> {extract_domain(brokerage)}")
