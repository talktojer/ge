# Security Notice

## Environment File Removal

As of September 2026, previously committed environment files (`.env`, `env.example`, `env.prod.example`) containing sensitive configuration have been removed from the repository and added to `.gitignore`.

### Action Required

If you previously had access to this repository when environment files were committed:

1. **Rotate credentials**: Any API keys, database passwords, secret keys, or other sensitive values that were present in the committed `.env` files should be considered potentially exposed and should be rotated immediately.

2. **Review access logs**: Check your service provider access logs for any unauthorized access during the period when credentials were exposed.

3. **Update local configurations**: Ensure your local development environment uses secure, non-committed `.env` files going forward.

### Going Forward

- **Never commit secrets**: Environment files with real credentials must never be committed to version control
- **Use `.env.example` templates**: Commit only example/template files with placeholder values
- **Store secrets securely**: Use environment variables, secret management services, or encrypted credential stores
- **Rotate regularly**: Practice regular credential rotation as part of security hygiene

For questions or concerns, please contact the repository maintainers.
