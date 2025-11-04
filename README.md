# Radiohead's Dead Air Space Archive

https://radiohead.com/deadairspace

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
