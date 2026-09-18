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

Not yet supported: GitHub Copilot. It routes agent traffic through its own
backend and doesn't expose reliable local token counts — to be investigated
honestly before claiming support.

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

**Statut** : prototype précoce. Claude Code et Windsurf/Devin Desktop sont
couverts en détail, Codex CLI en version grossière. Cursor est marqué comme
**estimé** en permanence — son propre champ local `tokenCount` est documenté
comme peu fiable ailleurs, donc pas de fausse précision ici. Windsurf et
Cursor n'ont pas encore été vérifiés sur une vraie installation (ni l'un ni
l'autre n'est installé sur la machine où ce code a été écrit). Copilot n'est
pas encore supporté.
