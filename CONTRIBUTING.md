# Contributing

Thanks for your interest in contributing! Here's how to get started.

## Bug Reports & Feature Requests

Open a [GitHub Issue](../../issues/new) with:
- Clear description of the problem or idea
- Steps to reproduce (for bugs)
- Expected vs actual behavior

## Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Make your changes with clear commit messages
4. Run existing tests to ensure nothing breaks
5. Open a PR with a description of what changed and why

## Development Setup

See the README for installation and setup instructions.

## Verification

Use Python 3.12+ and Node 22.12+ (or 20.19+). From the repository root, create
the environment described in the README, then run the same checks as
[CI](.github/workflows/ci.yml):

```bash
source backend/venv/bin/activate
cd backend
python -m pytest tests/test_processor.py -q  # focused example; choose the changed module
python -m pytest                             # broader synthetic backend suite
cd ../frontend
npm ci
npm run lint
npm run build                                # TypeScript check plus Vite build
cd ..
```

The backend tests use authored data and temporary cache files. They do not run
browser discovery or the pipeline. There is no frontend test script or separate
format gate; lint and build are the existing frontend gates.

For changed dashboard behavior, run `npm run dev` from `frontend/` and use browser
tooling to intercept `/api/*` with synthetic responses shaped by
`backend/models.py`. Check the changed charts/filters, empty and error states,
and a narrow viewport. Keep mutation endpoints blocked. The repo has no automated
browser fixture harness; record that lane as unavailable if interception is not
available, rather than using personal history as a test fixture.

Do not start the backend or use `make dev`, `make install`, `make refresh`, or
`pipeline.py` for an offline verification pass: startup can discover/read browser
history, install activates launchd services, and refresh writes caches. AI
categorization can send domains to Anthropic when a key is present. Real-history
and provider checks need a separately chosen data/provider boundary.

## Code Style

- Follow the existing patterns in the codebase
- Use meaningful variable and function names
- Add comments only where the logic isn't self-evident

## Questions?

Open an issue or start a discussion. Response time is typically within a few days.
