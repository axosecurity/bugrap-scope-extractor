#!/usr/bin/env python3
import requests
import json
import re
import os
import time
from urllib.parse import urlparse

BASE_URL = "https://api.bugrap.io/api/v1/companies"

def get_companies():
    companies = []
    for page in range(1, 10):
        try:
            resp = requests.get(f"{BASE_URL}?page={page}&pageSize=52", timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("list", [])
            if not data:
                break
            companies.extend([c["name"] for c in data])
            time.sleep(2)  # Add delay between requests
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            time.sleep(5)
            continue
    return list(set(companies))

def categorize_scope_item(item):
    """Categorize scope item by type"""
    item = item.strip()
    
    # Remove backticks
    clean_item = item.strip('`')
    
    # Check for GitHub
    if 'github.com' in clean_item.lower():
        return 'github', clean_item
    
    # Check for Chrome/Extension
    if 'chrome' in clean_item.lower() or 'extension' in clean_item.lower() or 'webstore' in clean_item.lower() or 'firefox' in clean_item.lower() or 'edge' in clean_item.lower():
        return 'chrome', clean_item
    
    # Check for Etherscan/Smart Contract
    if 'etherscan' in clean_item.lower() or '0x' in clean_item or 'contract' in clean_item.lower() or 'blockchain' in clean_item.lower():
        return 'smartcontract', clean_item
    
    # Check for Wildcard domains (*.example.com)
    if clean_item.startswith('*.'):
        return 'wildcard', clean_item
    
    # Check for domain/web
    if clean_item.startswith('http://') or clean_item.startswith('https://'):
        domain = urlparse(clean_item).netloc or urlparse(clean_item).path
        return 'domains', domain if domain else clean_item
    elif '.' in clean_item and not ' ' in clean_item and not clean_item.startswith('|'):
        # Looks like a domain
        return 'domains', clean_item
    
    # Default to other
    return 'other', clean_item

def extract_in_scope_items(policy):
    """Extract in-scope items from markdown tables"""
    if not policy:
        return []
    
    in_scope = []
    lines = policy.split('\n')
    in_table = False
    in_header = False
    
    for line in lines:
        # Check for any table header with "In Scope" or "Scope" or "Asset"
        if '| In Scope' in line or '| In Scopes' in line or '|Scope|' in line or ('| Category' in line and '| Asset' in line):
            in_table = True
            in_header = True
            continue
        
        # Skip the separator line (---)
        if in_table and in_header and '---' in line:
            in_header = False
            continue
        
        if in_table and not in_header:
            # Process table rows
            if line.strip().startswith('|') and '--' not in line:
                parts = [p.strip() for p in line.split('|')]
                # Filter out empty parts
                cells = [p for p in parts if p]
                
                # For Category/Asset tables: grab the LAST column (Asset)
                # For other tables: grab non-empty content except headers
                if len(cells) >= 2:
                    # Get the last cell (Asset column)
                    content = cells[-1]
                    if content and content not in ['', 'Asset', 'Description', 'Category', 'In Scope', 'In Scopes']:
                        in_scope.append(content)
            # End table if we hit a non-table line
            elif line.strip() and not line.startswith('|') and line.strip().startswith('-'):
                continue
            elif line.strip() and not line.startswith('|'):
                in_table = False
    
    return in_scope

def get_scope(company_name):
    try:
        resp = requests.get(f"{BASE_URL}/{company_name}")
        data = resp.json().get("data", {})
        if not data:
            return None
        policy = data.get("policy", "")
        
        in_scope = extract_in_scope_items(policy)
        
        return {
            "name": data["name"],
            "description": data.get("description", ""),
            "url": f"https://bugrap.io/bounties/{company_name}",
            "in_scope": in_scope,
            "policy": policy[:500] + "..." if len(policy) > 500 else policy
        }
    except Exception as e:
        print(f"Error processing {company_name}: {e}")
        return None

def save_categorized_files(results):
    """Save inscope items to separate files by category"""
    categories = {
        'domains': set(),
        'wildcard': set(),
        'github': set(),
        'chrome': set(),
        'smartcontract': set(),
        'other': set()
    }
    
    company_map = {}
    
    # Categorize all items
    for result in results:
        company_name = result['name']
        company_map[company_name] = {'domains': set(), 'wildcard': set(), 'github': set(), 
                                     'chrome': set(), 'smartcontract': set(), 'other': set()}
        
        for item in result['in_scope']:
            category, value = categorize_scope_item(item)
            categories[category].add(value)
            company_map[company_name][category].add(value)
    
    # Create output directory
    os.makedirs('bugrap_output', exist_ok=True)
    
    # Save global files
    for category, items in categories.items():
        if items:
            filename = f'bugrap_output/{category}.txt'
            with open(filename, 'w') as f:
                f.write('\n'.join(sorted(items)))
            print(f"Saved {len(items)} items to {filename}")
    
    # Save per-company files
    os.makedirs('bugrap_output/by_company', exist_ok=True)
    for company_name, categories_data in company_map.items():
        for category, items in categories_data.items():
            if items:
                filename = f'bugrap_output/by_company/{company_name}_{category}.txt'
                with open(filename, 'w') as f:
                    f.write('\n'.join(sorted(items)))
    
    print(f"\nCreated per-company files in bugrap_output/by_company/")

# Main execution
companies = get_companies()
print(f"Found {len(companies)} companies")

results = []
for i, name in enumerate(companies):
    print(f"[{i+1}/{len(companies)}] Processing: {name}")
    try:
        scope = get_scope(name)
        if scope:
            results.append(scope)
        time.sleep(1)  # Add delay between requests
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)

# Save JSON
with open("bugrap_scopes.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to bugrap_scopes.json")

# Save categorized files
save_categorized_files(results)
print(f"\nCategorized files saved to bugrap_output/")
