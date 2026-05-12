================================================================================
                    BUGRAP SCOPE EXTRACTOR - WORKFLOW GUIDE
================================================================================

PROJECT OVERVIEW
================================================================================
This tool extracts in-scope targets from BugRap bounty programs and categorizes 
them into separate, organized text files for easy reference and analysis.

WHAT IT DOES
================================================================================
The script performs the following workflow:

1. FETCH COMPANIES
   - Fetches list of all active bug bounty companies from BugRap API
   - Paginates through results to collect all companies
   - Removes duplicates

2. EXTRACT POLICIES
   - For each company, fetches their complete bounty policy
   - Parses markdown tables to identify "In Scope" items
   - Extracts all scoped targets/assets

3. CATEGORIZE TARGETS
   - Analyzes each in-scope item and categorizes by type:
     * domains.txt      → Web domains and web store links
     * wildcard.txt     → Wildcard domains (*.example.com)
     * github.txt       → GitHub repository links
     * chrome.txt       → Chrome extension and web store links
     * smartcontract.txt → Ethereum smart contracts and Etherscan links
     * other.txt        → Miscellaneous items

4. SAVE OUTPUT FILES
   - Global files in bugrap_output/ with all collected items
   - Per-company files in bugrap_output/by_company/ organized by company

5. JSON BACKUP
   - Saves complete raw data to bugrap_scopes.json for reference

OUTPUT FILES STRUCTURE
================================================================================

bugrap_output/
├── domains.txt          # All web domains from all companies
├── wildcard.txt         # All wildcard domains (*.domain.com)
├── github.txt           # All GitHub repository links
├── chrome.txt           # Chrome extensions and web store links
├── smartcontract.txt    # Smart contracts and Etherscan links
├── other.txt            # Other/miscellaneous items
└── by_company/
    ├── ZKSAFE_domains.txt
    ├── ZKSAFE_wildcard.txt
    ├── ZKSAFE_github.txt
    ├── ZKSAFE_chrome.txt
    ├── ZKSAFE_smartcontract.txt
    ├── ZKSAFE_other.txt
    ├── PROJECT2_domains.txt
    ├── PROJECT2_wildcard.txt
    ... (continues for each company)

QUICK START
================================================================================

1. Install dependencies:
   pip install requests

2. Run the extractor:
   python3 extract_bugrap.py

3. Wait for completion:
   - Script will display progress: [1/50] Processing: COMPANY_NAME
   - All API calls are made in sequence
   - Total time depends on number of companies (typically 2-5 minutes)

4. Review results:
   - Check bugrap_output/ for categorized files
   - Each file contains one item per line
   - Files are sorted alphabetically and deduplicated

USAGE EXAMPLES
================================================================================

View all in-scope domains:
   cat bugrap_output/domains.txt

View wildcard domains:
   cat bugrap_output/wildcard.txt

View GitHub repositories:
   cat bugrap_output/github.txt

Count total domains across all companies:
   wc -l bugrap_output/domains.txt

Get ZKSAFE-specific smart contracts:
   cat bugrap_output/by_company/ZKSAFE_smartcontract.txt

Search for specific company domains:
   grep -r "specific-domain" bugrap_output/by_company/

HOW IT CATEGORIZES ITEMS
================================================================================

DOMAINS
   - Items containing domain extensions (.com, .io, etc.)
   - HTTP(S) URLs
   - Identified by TLD pattern
   Example: app.zksafe.pro, example.com

WILDCARD DOMAINS
   - Items starting with wildcard operator (*)
   - Pattern: *.domain.com
   Example: *.example.io

GITHUB
   - URLs containing "github.com"
   - Repository links
   Example: https://github.com/ZKSAFE/all-contracts

CHROME EXTENSIONS
   - URLs containing "chrome" or "webstore"
   - Extension references
   Example: https://chrome.google.com/webstore/detail/zksafe/...

SMART CONTRACTS
   - Etherscan links
   - Ethereum addresses (starting with 0x)
   - Contract-related items
   Example: https://etherscan.io/address/0x8528d5a...

OTHER
   - Items that don't match any category above

DATA SOURCES
================================================================================
API: https://api.bugrap.io/api/v1/companies/
Website: https://bugrap.io/

EXAMPLE: ZKSAFE BOUNTY
================================================================================
When processing ZKSAFE bounty from https://bugrap.io/bounties/ZKSAFE:

In-Scope Items from Table:
├── Web: Domain         → app.zksafe.pro        (domains.txt)
├── Chrome: Web Store   → [link]                (chrome.txt)
├── Source Code         → [GitHub link]         (github.txt)
└── Smart Contract      → [Etherscan link]      (smartcontract.txt)

Result:
├── bugrap_output/domains.txt         → app.zksafe.pro
├── bugrap_output/chrome.txt          → [extension link]
├── bugrap_output/github.txt          → https://github.com/ZKSAFE/all-contracts
├── bugrap_output/smartcontract.txt   → https://etherscan.io/address/0x8528d5a...
└── bugrap_output/by_company/
    ├── ZKSAFE_domains.txt            → app.zksafe.pro
    ├── ZKSAFE_chrome.txt
    ├── ZKSAFE_github.txt
    └── ZKSAFE_smartcontract.txt

TECHNICAL DETAILS
================================================================================

Parsing Strategy:
- Looks for markdown table headers: "| In Scopes", "| In Scope", "|Scope|"
- Extracts content from table rows between pipes (|)
- Stops parsing when table ends (non-pipe line found)

Deduplication:
- Global files remove duplicates across all companies
- Sets are used for fast deduplication
- Output is sorted alphabetically

Error Handling:
- Errors for individual companies don't stop execution
- Error messages printed with company name
- Script continues with remaining companies

NOTES
================================================================================

- API calls are sequential (not concurrent) to respect API limits
- Duplicate domains across different companies are deduplicated in global files
- Per-company files preserve exact formatting from policies
- Output files are UTF-8 encoded, newline-separated
- Items are deduplicated and sorted before saving

TROUBLESHOOTING
================================================================================

Issue: "Module 'requests' not found"
Solution: pip install requests

Issue: Connection errors
Solution: Check internet connection, verify API is accessible

Issue: Empty output files
Solution: API might be down or companies might have no policies

Issue: Some items appear in "other.txt"
Solution: These items don't match standard patterns. Manually review or
        adjust categorization in the categorize_scope_item() function

API RATE LIMITS
================================================================================
BugRap API generally allows ~1-2 requests per second. The script respects this
by making sequential requests. For large-scale automation, consider adding delays:

import time
time.sleep(1)  # Add between requests if needed

================================================================================
Last Updated: 2026
For updates, visit: https://bugrap.io/
================================================================================
