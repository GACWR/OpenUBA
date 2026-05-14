# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.0.2   | Yes       |
| < 0.0.2 | No        |

## Reporting a Vulnerability

The OpenUBA team takes security seriously. If you discover a security vulnerability, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

### How to Report

1. Email: info@gacwr.org
2. Subject: `[SECURITY] OpenUBA Vulnerability Report`
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix/Mitigation**: Depends on severity
  - Critical: 7 days
  - High: 14 days
  - Medium: 30 days
  - Low: Next release

### Disclosure Policy

- We will coordinate disclosure with the reporter
- We aim to release a fix before public disclosure
- Credit will be given to reporters (unless they prefer anonymity)

## Security Best Practices for Deployment

- Run OpenUBA behind a reverse proxy with TLS
- Use Kubernetes RBAC to restrict access to OpenUBA pods
- Store Elasticsearch and PostgreSQL credentials in Kubernetes Secrets
- Enable network policies to restrict pod-to-pod communication
- Regularly update container images for security patches
