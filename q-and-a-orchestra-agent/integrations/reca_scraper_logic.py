#!/usr/bin/env python3
"""
RECA ProCheck Scraper Logic - Integrated version for Agent Orchestra.
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import re
import string
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

BASE_URL = "https://reports.myreca.ca/publicsearch.aspx"

class RECAHttpScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })
        self._base_form_data: Dict[str, str] = {}
        self._initialized = False
    
    def _fetch_initial_state(self) -> None:
        """
        Two-step initialization:
        1. GET landing page.
        2. POST 'Button1' (Search by Person).
        3. Save resulting state as base for searches.
        """
        resp = self.session.get(BASE_URL, timeout=30)
        soup = BeautifulSoup(resp.content, 'html.parser')
        inputs = self._extract_all_inputs(soup)
        
        payload = inputs.copy()
        payload['Button1'] = 'Search by Person'
        
        for k in list(payload.keys()):
            if k in ['Button2', 'Button3']:
                del payload[k]
        
        resp2 = self.session.post(BASE_URL, data=payload, timeout=30)
        
        if self._is_error_response(resp2.text):
            raise Exception("Failed to initialize search session")
            
        self._update_state(resp2.content)
        self._initialized = True
        
    def _update_state(self, content: bytes) -> None:
        """Parse all form inputs from response."""
        soup = BeautifulSoup(content, 'html.parser')
        self._base_form_data = self._extract_all_inputs(soup)
    
    def _extract_all_inputs(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all valid form inputs for POST."""
        form_data = {}
        for inp in soup.find_all('input'):
            name = inp.get('name')
            if not name:
                continue
            
            inp_type = inp.get('type', 'text').lower()
            value = inp.get('value', '')
            
            if inp_type in ['hidden', 'text', 'password', 'search']:
                form_data[name] = value
            elif inp_type in ['checkbox', 'radio']:
                if inp.get('checked'):
                    form_data[name] = value
            
        for select in soup.find_all('select'):
            name = select.get('name')
            if not name:
                continue
            selected = select.find('option', selected=True)
            if selected:
                form_data[name] = selected.get('value', '')
            else:
                first_opt = select.find('option')
                if first_opt:
                    form_data[name] = first_opt.get('value', '')
        
        return form_data
    
    def _is_error_response(self, html: str) -> bool:
        """Check if response indicates error/ratelimit."""
        html_lower = html.lower()
        error_indicators = [
            "runtime error", 
            "server error in '/' application",
            "invalid postback",
            "event validation",
            "too many requests", "captcha", "blocked"
        ]
        return any(ind in html_lower for ind in error_indicators)
    
    def search_by_lastname(self, lastname: str) -> List[Dict]:
        """Search for agents by last name prefix."""
        if not self._initialized:
            self._fetch_initial_state()
        
        form_data = self._base_form_data.copy()
        form_data["TextBox2"] = lastname
        form_data["Button3"] = "Search"
        
        resp = self.session.post(BASE_URL, data=form_data, timeout=120) 
        
        if self._is_error_response(resp.text):
            raise Exception(f"Error response for '{lastname}'")
        
        self._update_state(resp.content)
        
        agents = self._parse_results(resp.text, lastname)
        return agents
    
    def _parse_results(self, html: str, query: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        agents = []
        
        header_td = soup.find('div', string=lambda t: t and "Licence History" in t)
        if not header_td:
            return []
            
        header_row = header_td.find_parent('tr')
        if not header_row:
             return []
             
        data_table = header_row.find_parent('table')
        if not data_table:
             return []
             
        rows = data_table.find_all('tr', recursive=False)
        
        try:
            header_idx = rows.index(header_row)
        except ValueError:
            header_idx = -1
            
        if header_idx == -1:
             return []
             
        for tr in rows[header_idx+1:]:
            cols = tr.find_all('td', recursive=False)
            if len(cols) < 10:
                continue
                
            def get_text(idx):
                if idx >= len(cols): return ""
                return cols[idx].get_text(" ", strip=True)

            status = get_text(0)
            
            # Extract Drillthrough ID if possible
            drill_id = ""
            view_link = cols[1].find('a') if len(cols) > 1 else None
            if view_link:
                onclick = view_link.get('onclick', '')
                match = re.search(r"InvokeReportAction\('Drillthrough','([^']+)'", onclick)
                if match:
                    drill_id = match.group(1)

            first = get_text(2)
            middle = get_text(3)
            last = get_text(4)
            aka = get_text(5)
            brokerage = get_text(6)
            city = get_text(7).title()
            
            if "Licensed" not in status and "suspended" not in status.lower() and "cancelled" not in status.lower():
                continue

            full_name = f"{first} {middle} {last}".replace("  ", " ").strip()
            
            agent = {
                "name": full_name,
                "first_name": first,
                "middle_name": middle,
                "last_name": last,
                "status": status,
                "brokerage": brokerage,
                "city": city,
                "sector": get_text(10),
                "aka": aka,
                "drill_id": drill_id
            }
            agents.append(agent)
            
        return agents

    def perform_drillthrough(self, drill_id: str) -> Optional[Dict[str, str]]:
        """
        Execute drillthrough to get detail page and extract contact info.
        Returns dict with 'email' and 'phone' keys, or None if request fails.
        """
        if not self._initialized:
            self._fetch_initial_state()
            
        form_data = self._base_form_data.copy()
        target = "ReportViewer1$ctl13$ReportControl$ctl00"
        
        form_data['__EVENTTARGET'] = target
        form_data['__EVENTARGUMENT'] = f"Drillthrough${drill_id}"
        
        # Remove buttons
        if 'Button3' in form_data: del form_data['Button3']
        if 'Button1' in form_data: del form_data['Button1']
        
        resp = self.session.post(BASE_URL, data=form_data, timeout=60)
        html = resp.text
        
        contact_info = {"email": None, "phone": None}
        
        # Extract email - try mailto link first
        email_match = re.search(r'mailto:([\w\.-]+@[\w\.-]+\.\w+)', html)
        if email_match:
            contact_info["email"] = email_match.group(1)
        else:
            # Fallback to general email regex
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', html)
            if emails:
                contact_info["email"] = emails[0]
        
        # Extract phone - try common patterns
        # Patterns: (403) 555-1234, 403-555-1234, 403.555.1234, 4035551234
        phone_patterns = [
            r'\((\d{3})\)\s*(\d{3})[-.]\s*(\d{4})',  # (403) 555-1234
            r'(\d{3})[-.]\s*(\d{3})[-.]\s*(\d{4})',  # 403-555-1234 or 403.555.1234
            r'(\d{3})[\s.](\d{3})[\s.](\d{4})',      # 403 555 1234
            r'(\d{10})',                              # 4035551234
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, html)
            if phone_match:
                groups = phone_match.groups()
                if len(groups) == 3:
                    contact_info["phone"] = f"({groups[0]}) {groups[1]}-{groups[2]}"
                elif len(groups) == 1 and len(groups[0]) == 10:
                    # Format 10-digit number
                    num = groups[0]
                    contact_info["phone"] = f"({num[:3]}) {num[3:6]}-{num[6:]}"
                break
        
        return contact_info
