---
name: cyber-implementing-jwt-signing-and-verification-53f5feff
description: Implements secure JWT (RFC 7519) signing and verification using HMAC-SHA256, RSA-PSS, ES256, and EdDSA, including token expiration, claims validation, and defenses against algorithm-confusion, none-algorithm, and key-injection attacks. Use when adding or hardening JWT-based authentication/authorization, or when auditing token verification code for common JWT vulnerabilities.
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

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/implementing-jwt-signing-and-verification/SKILL.md

Use manage_skills action=view_ref for supporting files, relative to this skill directory. In SOL-Lite use the workspace file tools at the skill path. Check required commands, libraries, credentials and tool availability before execution. Upstream tool/agent names are workflow examples: use the equivalent configured SOL tool. Skill instructions do not grant permissions or bypass host policy. If a dependency is missing, report it and the next setup step; do not claim execution succeeded. Original metadata and license terms are retained in UPSTREAM-SKILL.md and _licenses/.

# Implementing JWT Signing and Verification

## Overview

JSON Web Tokens (JWT) defined in RFC 7519 are compact, URL-safe tokens used for authentication and authorization in web applications. This skill covers implementing secure JWT signing with HMAC-SHA256, RSA-PSS, and EdDSA algorithms, along with verification, token expiration, claims validation, and defense against common JWT attacks (algorithm confusion, none algorithm, key injection).


## When to Use

- When deploying or configuring implementing jwt signing and verification capabilities in your environment
- When establishing security controls aligned to compliance requirements
- When building or improving security architecture for this domain
- When conducting security assessments that require this implementation

## Prerequisites

- Familiarity with cryptography concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Objectives

- Implement JWT signing with HS256, RS256, ES256, and EdDSA
- Verify JWT signatures and validate standard claims
- Implement token expiration, not-before, and audience validation
- Defend against algorithm confusion and none algorithm attacks
- Implement JWT key rotation with JWK Sets
- Build a complete authentication middleware

## Key Concepts

### JWT Algorithms

| Algorithm | Type | Key | Security Level |
|-----------|------|-----|---------------|
| HS256 | Symmetric (HMAC) | Shared secret | 128-bit |
| RS256 | Asymmetric (RSA) | RSA key pair | 112-bit |
| ES256 | Asymmetric (ECDSA) | P-256 key pair | 128-bit |
| EdDSA | Asymmetric (Ed25519) | Ed25519 pair | 128-bit |

### Common JWT Attacks

- **Algorithm confusion**: Switching from RS256 to HS256, using public key as HMAC secret
- **None algorithm**: Setting alg=none to bypass signature verification
- **Key injection**: Embedding key in JWK header
- **Weak secrets**: Brute-forcing short HMAC secrets
- **Token replay**: Reusing valid tokens without expiration

## Security Considerations

- Always validate the algorithm header against an allowlist
- Never accept alg=none in production
- Use asymmetric algorithms (RS256, ES256) for distributed systems
- Set short expiration times (15 min for access tokens)
- Implement token refresh mechanism
- Store secrets securely (not in source code)

## Validation Criteria

- [ ] JWT signing produces valid tokens for all algorithms
- [ ] Signature verification rejects tampered tokens
- [ ] Expired tokens are rejected
- [ ] Algorithm confusion attack is prevented
- [ ] None algorithm is rejected
- [ ] JWK key rotation works correctly
- [ ] Claims validation enforces all required claims

