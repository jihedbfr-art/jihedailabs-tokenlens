# jihedailabs-tokenlens

[![CI](https://github.com/jihedbfr-art/jihedailabs-tokenlens/actions/workflows/ci.yml/badge.svg)](https://github.com/jihedbfr-art/jihedailabs-tokenlens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Coverage](badges/coverage.svg)](#tests)

A local, offline report of where your AI coding assistant tokens actually go.

Reads the session logs your tools already write to disk (`~/.claude/projects/`,
`~/.codex/`), never sends anything over the network, and prints a breakdown by
session, project, and model — including a rough split between the fixed
per-session cost (system prompt, tools, skills, `CLAUDE.md`) and the tokens
your actual conversation used.

Part of [JihedAiLabs](https://github.com/jihedbfr-art).

## Why

Most "save tokens" tools focus on shrinking context. This one starts a step
earlier: you can't optimize what you haven't measured. Before deciding what to
cut, know what's actually costing you.

## Status

Early prototype. Currently supported:

- **Claude Code** — full breakdown (input / cache write / cache read / output).
  Verified against real local transcripts.
- **Codex CLI** — coarse per-thread totals only; Codex's local database does not
  split token types at that level, and the per-message log format hasn't been
  verified yet. No numbers are invented to fill the gap.
- **Windsurf / Devin Desktop** — full breakdown, same fields as Claude Code.
  Windsurf was renamed Devin Desktop after Cognition's acquisition; the local
  database still uses the old product name internally. **Not verified against
  a real installation** — built from public documentation of the schema, not
  from a file this tool actually opened.
- **Cursor** — reported as **estimated**, always. Cursor stores a `tokenCount`
  field per chat message locally, but multiple independent projects that
  inspected it found it unreliable or unused — Cursor's real billed usage
  lives on their servers, not on disk. Treat these numbers as a rough shape,
  not a bill. Also not verified against a real installation.

- **GitHub Copilot CLI** — full breakdown, schema *confirmed* against a real
  local `~/.copilot/data.db` file (the `sessions` table really does carry
  `total_input_tokens` / `total_output_tokens` / `total_cached_tokens` /
  `total_reasoning_tokens`). That table was empty on the machine this was
  written on, so the column *values* are still unobserved — two mapping
  choices (cached → cache-read, reasoning → folded into output) are
  assumptions, spelled out in the code, not verified against real numbers
  yet. Only the Copilot CLI store is read; VS Code's `github.copilot-chat`
  extension keeps a separate, near-empty store with no usable data.

## Install

```bash
pip install -e .
```

## Usage

```bash
tokenlens
```

## Tests

```bash
pip install -e ".[test]"
pytest --cov=tokenlens --cov-report=term-missing
```

Every parser is tested against a real temporary SQLite/JSONL file built in
the test itself — not a mock of the parsing logic — including the
"schema doesn't match, return nothing" fallback path each one relies on.

The coverage badge above is regenerated automatically by CI on every push
to `master` (`badges/coverage.svg`, committed by the `coverage-badge` job)
— it always reflects the last real measurement, never a hand-typed number.

## Principles

- 100% local. No network calls, no telemetry, ever.
- No native dependencies — installs the same way on Windows, macOS, Linux.
- If a number can't be verified from real data, the tool says so instead of
  guessing.

## License

MIT

## Contact

contact@winnemchi.tn

---

## En français

Un rapport local et hors-ligne de la consommation réelle de tokens de vos
assistants IA de code. Lit les journaux de session déjà écrits sur disque par
vos outils, n'envoie rien sur le réseau, et affiche une répartition par
session, projet et modèle — avec une estimation du coût fixe (prompt système,
outils, skills, `CLAUDE.md`) par rapport au coût de la conversation elle-même.

**Pourquoi** : la plupart des outils "d'économie de tokens" cherchent à
réduire le contexte. Celui-ci commence une étape avant : on n'optimise pas ce
qu'on n'a pas mesuré.

**Statut** : prototype précoce. Claude Code, Windsurf/Devin Desktop et GitHub
Copilot CLI sont couverts en détail, Codex CLI en version grossière. Cursor
est marqué comme **estimé** en permanence — son propre champ local
`tokenCount` est documenté comme peu fiable ailleurs, donc pas de fausse
précision ici. Le schéma de Copilot CLI a été vérifié sur un vrai fichier
local (table vide, donc valeurs pas encore observées) ; Windsurf et Cursor
n'ont pas encore été vérifiés du tout (aucun des deux n'est installé sur la
machine où ce code a été écrit).
