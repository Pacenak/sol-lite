---
name: cyber-detecting-exfiltration-over-dns-with-zeek-56b346d1
description: Detect DNS-based data exfiltration by analyzing Zeek dns.log for high-entropy subdomains, oversized TXT/NULL records, and anomalous query volume or patterns. Use when investigating suspected DNS tunneling, covert C2 over DNS, or data exfiltration hidden in DNS queries against network traffic captured by Zeek.
category: ecosystem
tags:
- ecosystem
- security
- cyber
sectors:
- '*'
status: published
source: imported
version: 54a798831d22
---

## SOL runtime integration

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/detecting-exfiltration-over-dns-with-zeek/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Detecting Exfiltration over DNS with Zeek

## Overview

DNS tunneling and exfiltration is a technique used by attackers to bypass firewalls and DLP controls by encoding stolen data into DNS query subdomains. Legitimate DNS queries have predictable entropy and length patterns, while exfiltration queries contain encoded data with high Shannon entropy, unusually long subdomain labels, and high volumes of unique subdomains per parent domain.

This skill analyzes Zeek dns.log files (TSV format) to detect exfiltration indicators. The agent computes Shannon entropy for each subdomain component, identifies queries exceeding the 63-character DNS label limit, counts unique subdomains per parent domain, and flags domains that exceed configurable thresholds. These techniques detect tools like dnscat2, iodine, dns2tcp, and custom DNS tunneling implementations.


## When to Use

- When investigating security incidents that require detecting exfiltration over dns with zeek
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Python 3.9 or later with math and collections modules (stdlib)
- Zeek dns.log files in TSV format with standard field headers
- Network capture data processed by Zeek 5.0+ or later
- Understanding of DNS protocol structure and query types

## Steps

1. **Parse Zeek dns.log headers**: Read the TSV file, extract the `#fields` header line to identify column positions for `ts`, `id.orig_h`, `query`, `qtype_name`, `rcode_name`, and `answers`.

2. **Extract and decompose queries**: For each DNS query, split the FQDN into subdomain labels and parent domain. Skip queries to known safe domains and internal zones.

3. **Compute Shannon entropy**: Calculate the information entropy of each subdomain label. Legitimate subdomains typically have entropy below 3.5, while encoded/encrypted data produces entropy above 4.0.

4. **Detect long labels**: Flag DNS labels exceeding 52 characters (approaching the 63-character maximum). Long labels are a strong indicator of data tunneling.

5. **Count unique subdomains per domain**: Track how many distinct subdomains each parent domain receives. Domains with more than 50 unique subdomains within the log window are suspicious.

6. **Identify query volume anomalies**: Calculate queries-per-minute per source IP per domain. Exfiltration tools generate sustained high-volume query streams that differ from normal browsing.

7. **Score and rank domains**: Combine entropy, label length, uniqueness count, and query volume into a composite risk score. Rank domains by score and output the top suspicious domains.

8. **Generate detection report**: Produce a JSON report with flagged domains, their evidence indicators, originating source IPs, and recommended response actions.

## Expected Output

```json
{
  "analysis_summary": {
    "total_queries_analyzed": 145832,
    "unique_domains": 3421,
    "flagged_domains": 3,
    "entropy_threshold": 3.5
  },
  "flagged_domains": [
    {
      "domain": "data.evil-c2.com",
      "unique_subdomains": 892,
      "avg_entropy": 4.72,
      "max_label_length": 61,
      "source_ips": ["10.0.1.45"],
      "risk_score": 9.4,
      "indicators": ["high_entropy", "long_labels", "high_subdomain_count"]
    }
  ]
}
```

