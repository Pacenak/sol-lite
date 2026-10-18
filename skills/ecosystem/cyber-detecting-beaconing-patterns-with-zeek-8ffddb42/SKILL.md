---
name: cyber-detecting-beaconing-patterns-with-zeek-8ffddb42
description: Performs statistical analysis of Zeek conn.log connection intervals to detect C2 beaconing patterns. Uses the ZAT library to load Zeek logs into Pandas DataFrames, calculates inter-arrival time standard deviation, and flags periodic connections with low jitter. Use when hunting for command-and-control callbacks in network data.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/detecting-beaconing-patterns-with-zeek/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Detecting Beaconing Patterns with Zeek


## When to Use

- When investigating security incidents that require detecting beaconing patterns with zeek
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Load Zeek conn.log data using ZAT (Zeek Analysis Tools), group connections by
source/destination pairs, and compute timing statistics to identify beaconing.

```python
from zat.log_to_dataframe import LogToDataFrame
import numpy as np

log_to_df = LogToDataFrame()
conn_df = log_to_df.create_dataframe('/path/to/conn.log')

# Group by src/dst pair and calculate inter-arrival time
for (src, dst), group in conn_df.groupby(['id.orig_h', 'id.resp_h']):
    times = group['ts'].sort_values()
    intervals = times.diff().dt.total_seconds().dropna()
    if len(intervals) > 10:
        std_dev = np.std(intervals)
        mean_interval = np.mean(intervals)
        # Low std_dev relative to mean = likely beaconing
```

Key analysis steps:
1. Parse Zeek conn.log into DataFrame with ZAT LogToDataFrame
2. Group connections by source IP and destination IP pairs
3. Calculate inter-arrival time intervals between consecutive connections
4. Compute standard deviation and coefficient of variation
5. Flag pairs with low coefficient of variation as potential beacons

## Examples

```python
from zat.log_to_dataframe import LogToDataFrame
log_to_df = LogToDataFrame()
df = log_to_df.create_dataframe('conn.log')
print(df[['id.orig_h', 'id.resp_h', 'ts', 'duration']].head())
```

