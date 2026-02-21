import streamlit as st
import pandas as pd
import json
import os
import glob
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="RECA Enrichment Dashboard",
    page_icon="🏘️",
    layout="wide"
)

# Title
st.title("🏘️ RECA Agent Data Enrichment Dashboard")

# Sidebar
st.sidebar.header("Configuration")
data_dir = st.sidebar.text_input("Data Directory", "data")

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

# --- Section 1: Data Overview ---
st.header("📊 Data Overview")

# Load base data
base_data_path = os.path.join(data_dir, "all_agents.json")
agents_data = load_json(base_data_path)

if agents_data:
    total_agents = len(agents_data)
    
    # Calculate initial stats
    licensed_agents = sum(1 for a in agents_data if a.get('status') == 'Licensed')
    has_email = sum(1 for a in agents_data if a.get('email') or (a.get('contact_info') and a['contact_info'].get('email')))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Agents Scraped", f"{total_agents:,}")
    col2.metric("Licensed Agents", f"{licensed_agents:,}")
    col3.metric("Existing Emails", f"{has_email:,}", delta=f"{(has_email/total_agents)*100:.1f}%")
    
    # Show sample data
    with st.expander("View Raw Data Sample"):
        df = pd.DataFrame(agents_data)
        st.dataframe(df.head(10))
else:
    st.error(f"Could not load data from {base_data_path}")

# --- Section 2: Enrichment Results ---
st.header("✨ Enrichment Status")

enriched_path = os.path.join(data_dir, "all_agents_enriched.json")
enriched_data = load_json(enriched_path)

if enriched_data:
    enriched_total = len(enriched_data)
    enriched_success = sum(1 for a in enriched_data if a.get('enrichment', {}).get('email'))
    
    col1, col2 = st.columns(2)
    col1.metric("Agents Processed", f"{enriched_total:,}")
    col2.metric("Enrichment Success", f"{enriched_success:,}", delta=f"{(enriched_success/enriched_total)*100:.1f}% Match Rate")
    
    # Visualization of methods
    methods = {}
    for a in enriched_data:
        method = a.get('enrichment', {}).get('enrichment_method')
        if method:
            methods[method] = methods.get(method, 0) + 1
            
    if methods:
        st.subheader("Enrichment Methods")
        st.bar_chart(methods)
        
    # Download button
    st.download_button(
        label="Download Enriched Data (JSON)",
        data=json.dumps(enriched_data, indent=2),
        file_name="reca_agents_enriched.json",
        mime="application/json"
    )
else:
    st.info("No full enrichment run detected (all_agents_enriched.json not found).")

# --- Section 3: Scale Test Analysis ---
st.header("🧪 Recent Scale Tests")

# Find scale test results
test_files = glob.glob(os.path.join(data_dir, "scale_test_results_*.json"))
test_files.sort(key=os.path.getmtime, reverse=True)

if test_files:
    selected_test = st.selectbox("Select Test Run", test_files, format_func=lambda x: f"{os.path.basename(x)} ({datetime.fromtimestamp(os.path.getmtime(x)).strftime('%Y-%m-%d %H:%M')})")
    
    if selected_test:
        test_data = load_json(selected_test)
        
        if 'summary' in test_data:
            summary = test_data['summary']
            
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Batch Size", summary.get('total', 0))
            t2.metric("Success Rate", f"{(summary.get('success', 0) / summary.get('total', 1) * 100):.1f}%")
            t3.metric("Avg Time", f"{(summary.get('duration', 0) / summary.get('total', 1)):.2f}s")
            t4.metric("Errors", summary.get('errors', 0))
            
            # Show failures
            if summary.get('failed', 0) > 0:
                st.subheader("Failed Cases")
                failures = [r for r in test_data.get('results', []) if not r.get('emails')]
                if failures:
                    fail_df = pd.DataFrame([{
                        'Name': f['name'],
                        'Brokerage': f['brokerage'],
                        'Website': f.get('website', 'N/A'),
                        'Error': f.get('error', 'N/A')
                    } for f in failures])
                    st.dataframe(fail_df)
else:
    st.text("No scale test results found.")

# Footer
st.markdown("---")
st.caption("Q&A Orchestra Agent - RECA Dashboard v1.0")
