# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Unit tests covering every parser and the report aggregation logic.

## [0.1.0] - 2026-09-18

### Added
- Initial prototype: local, offline CLI that reports where AI coding
  assistant tokens go, with no network calls and no telemetry.
- **Claude Code** parser — full input/cache-write/cache-read/output
  breakdown, verified against real local transcripts.
- **Codex CLI** parser — coarse per-thread totals; documented as a floor,
  not a full breakdown, since the local database doesn't split token types
  at that level.
- **Cursor** parser — permanently marked as estimated; Cursor's own local
  `tokenCount` field is reported elsewhere as unreliable.
- **Windsurf / Devin Desktop** parser — full breakdown based on public
  documentation of the schema; not verified against a real installation.
- **GitHub Copilot CLI** parser — full breakdown; schema confirmed against
  a real local `~/.copilot/data.db` file, though the observed table was
  empty, so actual values are still unverified.
- Per-session fixed-cost estimate (system prompt + tools + skills +
  `CLAUDE.md`, derived from each session's first cache write).
- MIT license, bilingual (English/French) README.
