#!/usr/bin/env python3
import requests
import json
import re

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

def extract_scope_urls(policy):
    if not policy:
        return []
    urls = []
    # Extract GitHub repos
    urls.extend(re.findall(r'https://github\.com/[^\s\)]+', policy))
    # Extract domains
    urls.extend(re.findall(r'(?:https?://)?(?:[\w-]+\.)+[\w-]+[^\s\)]*', policy))
    return list(set(urls))

def get_scope(company_name):
    resp = requests.get(f"{BASE_URL}/{company_name}")
    data = resp.json()["data"]
    policy = data.get("policy", "")
    
    # Extract in-scope items from markdown tables
    in_scope = []
    lines = policy.split('\n')
    in_table = False
    for line in lines:
        if '| In Scope' in line or '|Scope|' in line:
            in_table = True
            continue
        if in_table:
            if line.strip().startswith('|') and '--' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[1] and parts[1] != 'Scope':
                    in_scope.append(parts[-1] if parts[-1] else parts[1])
            elif line.strip() and not line.startswith('|'):
                in_table = False
    
    return {
        "name": data["name"],
        "description": data.get("description", ""),
        "url": f"https://bugrap.io/bounties/{company_name}",
        "in_scope": in_scope,
        "policy": policy[:500] + "..." if len(policy) > 500 else policy
    }

companies = get_companies()
print(f"Found {len(companies)} companies")

results = []
for i, name in enumerate(companies):
    print(f"[{i+1}/{len(companies)}] Processing: {name}")
    try:
        scope = get_scope(name)
        results.append(scope)
    except Exception as e:
        print(f"Error: {e}")

with open("bugrap_scopes.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved to bugrap_scopes.json")
