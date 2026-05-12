#!/usr/bin/env python3
import requests
import json
import re
import os
from urllib.parse import urlparse

BASE_URL = "https://api.bugrap.io/api/v1/companies"

def get_companies():
    companies = []
    for page in range(1, 10):
        resp = requests.get(f"{BASE_URL}?page={page}&pageSize=52")
        data = resp.json()["data"]["list"]
        if not data:
            break
        companies.extend([c["name"] for c in data])
    return list(set(companies))

def categorize_scope_item(item):
    """Categorize scope item by type"""
    item = item.strip()
    
    # Check for GitHub
    if 'github.com' in item.lower():
        return 'github', item
    
    # Check for Chrome/Extension
    if 'chrome' in item.lower() or 'extension' in item.lower() or 'webstore' in item.lower():
        return 'chrome', item
    
    # Check for Etherscan/Smart Contract
    if 'etherscan' in item.lower() or '0x' in item or 'contract' in item.lower():
        return 'smartcontract', item
    
    # Check for domain/web
    if item.startswith('http://') or item.startswith('https://'):
        domain = urlparse(item).netloc or urlparse(item).path
        return 'domains', domain if domain else item
    elif '.' in item and not ' ' in item:
        # Looks like a domain
        return 'domains', item
    
    # Wildcard domains (*.example.com)
    if item.startswith('*.'):
        return 'wildcard', item
    
    # Default to other
    return 'other', item

def extract_in_scope_items(policy):
    """Extract in-scope items from markdown tables"""
    if not policy:
        return []
    
    in_scope = []
    lines = policy.split('\n')
    in_table = False
    
    for line in lines:
        # Check for table headers
        if '| In Scopes' in line or '| In Scope' in line or '|Scope|' in line:
            in_table = True
            continue
        
        if in_table:
            # Process table rows
            if line.strip().startswith('|') and '--' not in line:
                parts = [p.strip() for p in line.split('|')]
                # Filter out empty parts and headers
                if len(parts) >= 3:
                    for part in parts[1:-1]:  # Skip first and last (empty)
                        if part and part not in ['Scope', 'In Scopes', 'In Scope', '']:
                            in_scope.append(part)
            # End table if we hit a non-table line
            elif line.strip() and not line.startswith('|'):
                in_table = False
    
    return in_scope

def get_scope(company_name):
    resp = requests.get(f"{BASE_URL}/{company_name}")
    data = resp.json()["data"]
    policy = data.get("policy", "")
    
    in_scope = extract_in_scope_items(policy)
    
    return {
        "name": data["name"],
        "description": data.get("description", ""),
        "url": f"https://bugrap.io/bounties/{company_name}",
        "in_scope": in_scope,
        "policy": policy[:500] + "..." if len(policy) > 500 else policy
    }

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
        results.append(scope)
    except Exception as e:
        print(f"Error processing {name}: {e}")

# Save JSON
with open("bugrap_scopes.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to bugrap_scopes.json")

# Save categorized files
save_categorized_files(results)
print(f"\nCategorized files saved to bugrap_output/")
