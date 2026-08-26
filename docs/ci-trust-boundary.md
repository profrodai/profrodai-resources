# CI trust boundary

`verify-pr-safe` runs on `pull_request` and executes `make verify-pr`. It receives no secrets,
does not fetch `profrod-site`, and runs the credential-free committed-tree whitespace check,
catalog-structure validation, and all 11 course gates. Its structure-only catalog result must not
be read as proof that titles match the private source repository.

`verify-trusted-provenance` runs only after a push to `main` or by manual dispatch. It checks out
`main` explicitly, including on manual dispatch, then receives `PROFROD_SITE_READ_TOKEN` only to
fetch the pinned `rodriveracom/profrod-site` Git object. It resets the source remote to a
token-free URL before executing `make verify`. It never checks out or executes a pull-request ref.

Bootstrap limitation: a workflow newly introduced or edited in a pull request is not itself a
trusted control until the base branch contains it and branch protection requires that base-branch
PR-safe workflow. Review the workflow diff before merging; do not treat a PR's changed workflow
as proof of its own security.
