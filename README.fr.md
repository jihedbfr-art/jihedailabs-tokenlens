# jihedailabs-tokenlens

[![CI](https://github.com/jihedbfr-art/jihedailabs-tokenlens/actions/workflows/ci.yml/badge.svg)](https://github.com/jihedbfr-art/jihedailabs-tokenlens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Coverage](badges/coverage.svg)](#tests)

[🇬🇧 Read in English](README.md)

Un rapport local, hors ligne, de l'endroit où partent réellement les tokens de votre assistant de code.

L'outil lit les journaux de session que vos outils écrivent déjà sur disque (`~/.claude/projects/`, `~/.codex/`), n'envoie rien sur le réseau, et affiche une répartition par session, par projet et par modèle. Il estime aussi la part du coût fixe de chaque session (prompt système, outils, skills, `CLAUDE.md`) par rapport aux tokens de votre conversation proprement dite.

Fait partie de [JihedAiLabs](https://github.com/jihedbfr-art).

## Pourquoi

La plupart des outils « d'économie de tokens » cherchent à réduire le contexte. Celui-ci commence une étape plus tôt : on n'optimise pas ce qu'on n'a pas mesuré. Avant de décider quoi couper, il faut savoir ce qui coûte vraiment.

## Statut

Prototype précoce. Pris en charge pour l'instant :

- **Claude Code** : répartition complète (entrée / écriture cache / lecture cache / sortie). Vérifiée sur de vraies transcriptions locales.
- **Codex CLI** : totaux grossiers par fil uniquement. La base locale de Codex ne distingue pas les types de tokens à ce niveau, et le format du journal par message n'a pas encore été vérifié. Aucun chiffre n'est inventé pour combler le vide.
- **Windsurf / Devin Desktop** : répartition complète, mêmes champs que Claude Code. Windsurf a été rebaptisé Devin Desktop après le rachat par Cognition ; la base locale utilise encore l'ancien nom en interne. **Non vérifié sur une vraie installation** : le code vient de la documentation publique du schéma, pas d'un fichier réellement ouvert par l'outil.
- **Cursor** : toujours présenté comme **estimé**. Cursor stocke bien un champ `tokenCount` par message en local, mais plusieurs projets indépendants qui l'ont inspecté le jugent peu fiable ou inutilisé : l'usage réellement facturé vit sur les serveurs de Cursor, pas sur le disque. Prenez ces chiffres comme un ordre de grandeur, pas comme une facture. Non vérifié non plus sur une vraie installation.
- **GitHub Copilot CLI** : répartition complète, schéma *confirmé* sur un vrai fichier local `~/.copilot/data.db` (la table `sessions` contient bien `total_input_tokens`, `total_output_tokens`, `total_cached_tokens` et `total_reasoning_tokens`). Cette table était vide sur la machine où le code a été écrit : les *valeurs* des colonnes n'ont donc pas encore été observées, et deux choix de correspondance (cached → lecture cache, reasoning → ajouté à la sortie) sont des hypothèses, documentées dans le code, pas vérifiées sur de vrais chiffres. Seul le stockage de Copilot CLI est lu ; l'extension `github.copilot-chat` de VS Code garde un stockage séparé, presque vide et inexploitable.

## Installation

```bash
pip install -e .
```

## Utilisation

```bash
tokenlens
```

## Tests

```bash
pip install -e ".[test]"
pytest --cov=tokenlens --cov-report=term-missing
```

Chaque parseur est testé contre un vrai fichier SQLite/JSONL temporaire construit dans le test lui-même, et non contre un mock de la logique de parsing. Cela inclut le chemin de repli « le schéma ne correspond pas, ne rien renvoyer » sur lequel chacun s'appuie.

Le badge de couverture ci-dessus est régénéré automatiquement par la CI à chaque push sur `master` (`badges/coverage.svg`, commité par le job `coverage-badge`). Il reflète toujours la dernière mesure réelle, jamais un chiffre saisi à la main.

## Principes

- 100 % local. Aucun appel réseau, aucune télémétrie, jamais.
- Aucune dépendance native : s'installe de la même façon sous Windows, macOS et Linux.
- Si un chiffre ne peut pas être vérifié sur des données réelles, l'outil le dit au lieu de deviner.

## Licence

MIT

## Contact

contact@winnemchi.tn
