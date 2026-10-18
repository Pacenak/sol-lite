---
name: cyber-analyzing-ethereum-smart-contract-vulnerabil-2fd10d35
description: Perform static and symbolic analysis of Solidity smart contracts using Slither and Mythril to detect reentrancy, integer overflow, access control, and other vulnerability classes before deployment to Ethereum mainnet.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/analyzing-ethereum-smart-contract-vulnerabilities/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Analyzing Ethereum Smart Contract Vulnerabilities

## Overview

Smart contract vulnerabilities have led to billions of dollars in losses across DeFi protocols. Unlike traditional software, deployed smart contracts are immutable and handle real financial assets, making pre-deployment security analysis critical. Slither performs fast static analysis using an intermediate representation to detect over 90 vulnerability patterns in seconds, while Mythril uses symbolic execution and SMT solving to discover complex execution path vulnerabilities like reentrancy and integer overflows. This skill covers running both tools against Solidity contracts, interpreting results, triaging findings by severity, and generating audit reports.


## When to Use

- When investigating security incidents that require analyzing ethereum smart contract vulnerabilities
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Python 3.10+ with pip
- Slither (pip install slither-analyzer) and solc compiler
- Mythril (pip install mythril) with solc-select for compiler version management
- Solidity source code or compiled contract bytecode
- Foundry or Hardhat development framework (optional, for project-level analysis)

## Steps

### Step 1: Run Slither Static Analysis

Execute Slither against the contract codebase to identify vulnerability patterns, optimization opportunities, and code quality issues using its 90+ built-in detectors.

### Step 2: Run Mythril Symbolic Execution

Run Mythril deep analysis to explore execution paths and discover reentrancy, unchecked external calls, and arithmetic vulnerabilities that require path-sensitive analysis.

### Step 3: Triage and Correlate Findings

Combine results from both tools, deduplicate findings, assess severity based on exploitability and financial impact, and filter false positives.

### Step 4: Generate Audit Report

Produce a structured audit report with vulnerability descriptions, affected code locations, exploit scenarios, and remediation recommendations.

## Expected Output

JSON report listing vulnerabilities with SWC (Smart Contract Weakness Classification) identifiers, severity ratings, affected functions, and suggested fixes.

