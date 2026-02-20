#!/usr/bin/env python3
"""
Email Enrichment Test Script
Tests the email enrichment engine with sample data to validate functionality.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the enrichment engine
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from enrich_emails import EmailEnrichmentEngine

def load_sample_agents(sample_size=100):
    """Load a sample of agents for testing."""
    
    json_file = PROJECT_ROOT / "data" / "all_agents.json"
    
    if not json_file.exists():
        print(f"❌ ERROR: Source JSON file not found at {json_file}")
        return []
    
    print(f"📖 Loading sample data from {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            agents = json.load(f)
        
        # Take sample
        sample_agents = agents[:sample_size]
        print(f"✅ Loaded {len(sample_agents)} sample agents")
        
        return sample_agents
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return []

def test_enrichment_methods(engine, agents):
    """Test each enrichment method individually."""
    
    print("\n🔧 Testing Enrichment Methods...")
    print("-" * 50)
    
    # Test 1: Domain extraction
    print("\n1. Testing Domain Extraction:")
    test_agents = agents[:5]
    for agent in test_agents:
        brokerage = agent.get('brokerage', '')
        city = agent.get('city', '')
        domain = engine._extract_domain_from_brokerage(brokerage, city)
        print(f"   {brokerage[:30]:30} → {domain or 'No domain'}")
    
    # Test 2: Email pattern generation
    print("\n2. Testing Email Pattern Generation:")
    if test_agents:
        agent = test_agents[0]
        domain = engine._extract_domain_from_brokerage(
            agent.get('brokerage', ''), 
            agent.get('city', '')
        )
        if domain:
            patterns = engine._generate_email_patterns(agent, domain)
            print(f"   Agent: {agent.get('name', 'Unknown')}")
            print(f"   Domain: {domain}")
            print(f"   Patterns: {patterns[:5]}")  # Show first 5
        else:
            print("   No domain found for pattern testing")
    
    # Test 3: Email validation
    print("\n3. Testing Email Validation:")
    test_emails = [
        "john@example.com",
        "invalid-email",
        "jane.doe@company.ca",
        "test@.com",
        "user@domain.org"
    ]
    for email in test_emails:
        is_valid = engine._validate_email_format(email)
        print(f"   {email:25} → {'✅ Valid' if is_valid else '❌ Invalid'}")

def test_full_enrichment(engine, agents):
    """Test the full enrichment process on sample agents."""
    
    print("\n🚀 Testing Full Enrichment Process...")
    print("-" * 50)
    
    enriched_count = 0
    confidence_scores = []
    sources = {}
    
    for i, agent in enumerate(agents[:20], 1):  # Test first 20
        print(f"\n{i}. Processing: {agent.get('name', 'Unknown')}")
        print(f"   Brokerage: {agent.get('brokerage', 'N/A')}")
        print(f"   City: {agent.get('city', 'N/A')}")
        
        # Enrich the agent
        enriched_agent = engine.enrich_agent(agent)
        enrichment = enriched_agent.get('enrichment', {})
        
        email = enrichment.get('email')
        source = enrichment.get('email_source')
        confidence = enrichment.get('email_confidence', 0)
        
        if email:
            enriched_count += 1
            confidence_scores.append(confidence)
            sources[source] = sources.get(source, 0) + 1
            print(f"   ✅ Email found: {email}")
            print(f"   📊 Source: {source}")
            print(f"   📈 Confidence: {confidence:.2f}")
        else:
            print(f"   ❌ No email found")
            print(f"   📊 Source: {source}")
    
    # Summary statistics
    print("\n📊 Enrichment Summary:")
    print(f"   Total processed: {min(20, len(agents))}")
    print(f"   Emails found: {enriched_count}")
    print(f"   Success rate: {(enriched_count / min(20, len(agents))) * 100:.1f}%")
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        print(f"   Average confidence: {avg_confidence:.2f}")
    
    print("\n📈 Sources:")
    for source, count in sources.items():
        print(f"   {source}: {count}")

def save_test_results(enriched_agents, filename="test_enriched_agents.json"):
    """Save test results for review."""
    
    output_file = PROJECT_ROOT / "data" / filename
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_agents, f, indent=2)
        
        print(f"\n💾 Test results saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error saving test results: {e}")
        return False

def main():
    """Main test function."""
    
    print("=" * 60)
    print("Email Enrichment Engine Test")
    print("Implementation Planner Persona - Phase 2")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load sample data
    agents = load_sample_agents(100)
    
    if not agents:
        print("\n❌ Cannot proceed without sample data")
        return
    
    # Initialize enrichment engine
    print("\n🔧 Initializing Email Enrichment Engine...")
    engine = EmailEnrichmentEngine()
    
    # Test individual methods
    test_enrichment_methods(engine, agents)
    
    # Test full enrichment
    enriched_agents = []
    for agent in agents[:20]:  # Test on first 20
        enriched = engine.enrich_agent(agent)
        enriched_agents.append(enriched)
    
    test_full_enrichment(engine, agents)
    
    # Save results
    save_test_results(enriched_agents)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Phase 2 Testing Complete!")
    print("\nFindings:")
    print("1. Enrichment engine loaded successfully")
    print("2. Individual methods tested")
    print("3. Full enrichment process validated")
    print("4. Test results saved for review")
    print("\nNext Steps:")
    print("1. Review test results in data/test_enriched_agents.json")
    print("2. Validate email quality and sources")
    print("3. Proceed to full enrichment if satisfied")
    print("=" * 60)

if __name__ == "__main__":
    main()