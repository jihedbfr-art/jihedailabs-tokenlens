# jihedailabs-tokenlens

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
- **Codex CLI** — coarse per-thread totals only; Codex's local database does not
  split token types at that level, and the per-message log format hasn't been
  verified yet. No numbers are invented to fill the gap.

Not yet supported: Cursor, Windsurf, GitHub Copilot. These tools route agent
traffic through their own backend and don't expose reliable local token counts
— to be investigated honestly before claiming support.

## Install

```bash
pip install -e .
```

## Usage

```bash
tokenlens
```

## Principles

- 100% local. No network calls, no telemetry, ever.
- No native dependencies — installs the same way on Windows, macOS, Linux.
- If a number can't be verified from real data, the tool says so instead of
  guessing.

## License

MIT

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

**Statut** : prototype précoce. Claude Code est couvert en détail, Codex CLI
en version grossière (limite documentée honnêtement ci-dessus, pas de chiffre
inventé). Cursor, Windsurf et Copilot ne sont pas encore supportés.
