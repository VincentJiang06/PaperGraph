# dsh-academic-fetch

DSH bundle. Registers one tool, `academic_fetch`, which fetches an academic source and
writes a six-field **evidence anchor** into `result.data.meta.evidence`:

```
url · http_status · retrieved_at · extractor_version · object_sha256 · locator
```

The anchor is what makes a later quote checkable. The tool never judges whether a source
supports a claim — that decision belongs to the gate chain, not to the fetcher (W-02).

Illegal fetches (non-200, empty body, missing extractor version) are rejected at fetch
time rather than becoming silent empty evidence.

Install: this bundle ships with the `academic-research` profile; see `profile/install.sh`.
