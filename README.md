# Dead Air Space Archive

## Output Layout
```
archive/
  manifest.json
  state.json
  posts/
    <slug>/
      post.json
      index.md
      images/
      assets/
```

`manifest.json` aggregates per-post metadata and checksums, while `state.json` is written to support resumable crawls.
