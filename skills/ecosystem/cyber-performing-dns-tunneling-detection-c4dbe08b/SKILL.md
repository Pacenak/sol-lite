---
name: cyber-performing-dns-tunneling-detection-c4dbe08b
description: Detects DNS tunneling by computing Shannon entropy of DNS query names, analyzing query length distributions, inspecting TXT record payloads, and identifying high subdomain cardinality. Uses scapy for packet capture analysis and statistical methods to distinguish legitimate DNS from covert channels. Use when hunting for data exfiltration.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/performing-dns-tunneling-detection/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Performing DNS Tunneling Detection


## When to Use

- When conducting security assessments that involve performing dns tunneling detection
- When following incident response procedures for related security events
- When performing scheduled security testing or auditing activities
- When validating security controls through hands-on testing

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Analyze DNS traffic for indicators of DNS tunneling using entropy analysis and
statistical methods on query name characteristics.

```python
import math
from collections import Counter

def shannon_entropy(data):
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    return -sum((c/length) * math.log2(c/length) for c in counter.values())

# Legitimate domain: low entropy (~3.0-3.5)
print(shannon_entropy("www.google.com"))
# DNS tunnel: high entropy (~4.0-5.0)
print(shannon_entropy("aGVsbG8gd29ybGQ.tunnel.example.com"))
```

Key detection indicators:
1. High Shannon entropy in query names (> 3.5 for subdomain labels)
2. Unusually long query names (> 50 characters)
3. High volume of TXT record requests to a single domain
4. High unique subdomain count per parent domain
5. Non-standard character distribution in labels

## Examples

```python
from scapy.all import rdpcap, DNS, DNSQR
packets = rdpcap("dns_traffic.pcap")
for pkt in packets:
    if pkt.haslayer(DNSQR):
        query = pkt[DNSQR].qname.decode()
        entropy = shannon_entropy(query)
        if entropy > 4.0:
            print(f"Suspicious: {query} (entropy={entropy:.2f})")
```

