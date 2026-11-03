# Continuous Integration and Releases

Flockwise uses GitHub Actions to keep the main branch deployable and to publish immutable container releases.

## Continuous Integration

`.github/workflows/ci.yml` runs for pull requests, pushes to `main`, manual dispatches, and release verification. It:

- lints, format-checks, and tests Django against PostgreSQL 17 and Redis 8;
- installs the frontend with `npm ci`, type-checks it, rejects high or critical production dependency advisories, and creates a Nuxt production build;
- validates the private and cloud Compose files plus production shell scripts;
- performs an isolated database and attachment backup/restore rehearsal;
- builds the API and web production Docker targets without publishing them.

Protect `main` in GitHub and require the `Backend checks`, `Frontend checks`, `Validate deployment configuration`, `Rehearse backup and restore`, `Build API image`, and `Build web image` checks before merging. Workflows use read-only repository permissions unless publishing packages.

## Publishing a Release

The release workflow runs only for semantic-version tags matching `v*.*.*`. Create a release from a clean, tested `main` branch:

```bash
git tag -a v0.1.0 -m "Flockwise v0.1.0"
git push origin v0.1.0
```

After CI passes, GitHub Actions publishes multi-architecture images to:

- `ghcr.io/<owner>/flockwise-api`
- `ghcr.io/<owner>/flockwise-web`

Each release receives the full version, major/minor, commit-SHA, and—when applicable—`latest` tags. Images include SBOM and provenance attestations. Prefer the digest shown by GHCR in `.env.cloud` so deployments cannot silently change.

If packages are private, authenticate the cloud host with a read-only GitHub token before `docker compose pull`. Package visibility and token access are managed in the repository or organization package settings.

## Dependency Updates

Dependabot checks Python, npm, GitHub Actions, and Docker base images monthly. Review release notes, let CI validate the update, and avoid merging major upgrades without a focused compatibility test.
