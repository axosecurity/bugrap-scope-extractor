Bugrap Scope Extractor
=======================

A Python tool to extract bug bounty program scopes from Bugrap (https://bugrap.io).

What it does:
- Fetches all available companies from Bugrap's public API
- Retrieves each company's bug bounty scope details
- Parses markdown tables to extract in-scope targets (domains, GitHub repos, etc.)
- Saves results to bugrap_scopes.json

Usage:
    python3 extract_bugrap.py

Requirements:
    pip install requests

Output:
    bugrap_scopes.json - Contains array of company scope objects with:
      - name: Company name
      - description: Company description
      - url: Bugrap profile URL
      - in_scope: List of in-scope targets
      - policy: Bug bounty policy (truncated to 500 chars)

No authentication required - uses Bugrap's public API.