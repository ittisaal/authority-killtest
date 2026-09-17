# Candidate harvest v1

This stage precedes frozen V4 analysis.

It searches the public Sourcegraph index for GitHub repositories using a fixed set of GitHub custom-property / OIDC / property-authority signatures. Sourcegraph is used because its public streaming API supports large unauthenticated reproducible searches and returns the exact indexed commit for each file match.

Pipeline:

1. collect raw signature matches from Sourcegraph-indexed public GitHub repositories;
2. deduplicate by repository + exact commit + path;
3. apply only cheap structural filtering;
4. aggregate the surviving file hits to repository + exact commit candidates;
5. write canonical hashes for the candidate list.

Cheap filtering removes only obvious docs/tests/examples/demos/tutorials/fixtures/mocks, generated/vendor directories, README-style documentation, and lockfiles. It does not run V4 and it does not classify U/S/N.

The resulting counts describe a candidate-search universe, not ecosystem prevalence. Sourcegraph does not index every public GitHub repository, so the harvest must not be described as a census of GitHub.

After the run, the surviving candidate list and its digest are frozen before any V4 analysis is launched.
