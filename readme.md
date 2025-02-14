---

# LLM Code Review Action

Une GitHub Action réutilisable qui intègre un LLM (par exemple, Qwen2.5-coder) dans votre pipeline CI/CD pour réaliser une revue de code automatisée. L'action extrait le diff d'une pull request, segmente et filtre intelligemment le contenu, interroge le LLM pour obtenir des retours détaillés, ajuste et enrichit les numéros de ligne, et publie ensuite les commentaires sur la pull request.

---

## Table des Matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture du Projet](#architecture-du-projet)
- [Installation et Configuration](#installation-et-configuration)
- [Utilisation en Local](#utilisation-en-local)
- [Utilisation comme GitHub Action](#utilisation-comme-github-action)
- [Suppression des Commentaires](#suppression-des-commentaires)
- [Contribuer](#contribuer)
- [Licence](#licence)

---

## Fonctionnalités

- **Extraction intelligente du diff :**  
  - Récupération du diff via l'API GitHub.
  - Filtrage des fichiers indésirables (ex : fichiers de tests) avec des motifs modulables via une variable d'environnement.

- **Découpage intelligent du diff :**  
  - Découpage par bloc de fichier et subdivision par nombre de lignes pour s'adapter aux limites de traitement.

- **Interrogation du LLM :**  
  - Envoi de chaque segment au LLM pour obtenir des retours structurés.
  - Extraction robuste de la réponse JSON, même si le LLM renvoie du texte superflu.

- **Post-traitement des numéros de ligne :**  
  - Ajustement des numéros de ligne rapportés par le LLM en se basant sur les hunk headers du diff.

- **Publication des commentaires :**  
  - Mise en forme enrichie des commentaires avec code contextuel (récupéré via l'API GitHub) pour faciliter la compréhension par les développeurs.

- **Jobs complémentaires (optionnels) :**  
  - Jobs manuels pour supprimer automatiquement tous les commentaires d'une PR ou ceux générés par le workflow.

---

## Architecture du Projet

Le projet est organisé de manière modulaire :

- **main.py :**  
  Point d'entrée qui orchestre l'extraction du diff, l'interrogation du LLM, l'ajustement des numéros de ligne et la publication des commentaires.

- **config.py :**  
  Gestion centralisée de la configuration via un fichier `.env`.

- **diff_extractor.py :**  
  Contient les fonctions `get_diff_from_pr`, `filter_diff` et `split_diff_intelligent` pour récupérer et traiter le diff.

- **llm_client.py :**  
  Contient la fonction `query_llm` et des utilitaires comme `extract_json_from_text` et `adjust_line_number_from_diff`.

- **comment_publisher.py :**  
  Gère la publication des commentaires sur la pull request via l'API GitHub.

- **Scripts complémentaires :**  
  - `delete_pr_comments.py` pour supprimer tous les commentaires d'une PR.
  - `delete_workflow_comments.py` pour supprimer les commentaires spécifiques au dernier workflow.

- **action.yml :**  
  Fichier de définition de l'action réutilisable, placé à la racine ou dans un répertoire dédié.

---

## Installation et Configuration

### Prérequis

- [Python 3.7+](https://www.python.org/)
- Git
- Accès à l'API GitHub avec un token (via `GITHUB_TOKEN` ou un PAT) et un endpoint LLM.

### Configuration

1. **Cloner le dépôt :**

   ```bash
   git clone https://github.com/jo15122002/flair.git
   cd flair
   ```

2. **Créer un fichier `.env`** (ou configurer les variables d'environnement) avec par exemple :

   ```env
   LLM_ENDPOINT=https://your-llm.example.com/predict
   DIFF_CHUNK_SIZE=10000
   EXCLUDE_PATTERNS=test,tests,spec
   CI_PLATFORM=github
   # Ces variables seront automatiquement injectées par GitHub Actions dans le workflow consommateur :
   # GITHUB_REPOSITORY et GITHUB_PR_NUMBER
   ```

3. **Installer les dépendances :**

   ```bash
   pip install -r requirements.txt
   ```

---

## Utilisation en Local

Pour tester l'ensemble de la chaîne d'analyse et de publication :

1. Configurez vos variables d'environnement (soit via un fichier `.env`, soit directement dans le shell).
2. Lancez le script principal :

   ```bash
   python main.py
   ```

3. Exécutez les tests unitaires :

   ```bash
   pytest
   ```

---

## Utilisation comme GitHub Action

Vous pouvez transformer ce projet en une GitHub Action réutilisable.

### Exemple de fichier `action.yml` (placé à la racine ou dans un répertoire dédié) :

```yaml
name: "LLM Code Review Action"
description: "An automated code review action that uses an LLM to analyze diffs and post review comments on pull requests."
author: "Votre Nom ou Organisation"

inputs:
  llm-endpoint:
    description: "Endpoint URL of the LLM server (e.g., https://your-llm.example.com/predict)"
    required: true
  diff-chunk-size:
    description: "Maximum size for diff chunks (in lines or characters)"
    required: false
    default: "10000"
  exclude-patterns:
    description: "Comma-separated list of file patterns to exclude (e.g., test,tests,spec)"
    required: false
    default: "test,tests,spec"
  github-token:
    description: "GitHub token for authentication"
    required: true

runs:
  using: "composite"
  steps:
    - name: Checkout Repository
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install Dependencies
      shell: bash
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run LLM Code Review
      shell: bash
      env:
        GITHUB_TOKEN: ${{ inputs.github-token }}
        LLM_ENDPOINT: ${{ inputs.llm-endpoint }}
        DIFF_CHUNK_SIZE: ${{ inputs.diff-chunk-size }}
        EXCLUDE_PATTERNS: ${{ inputs.exclude-patterns }}
        CI_PLATFORM: github
        GITHUB_REPOSITORY: ${{ github.repository }}
        GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
      run: |
        python main.py
```

### Utilisation dans un projet consommateur :

Dans le workflow du projet consommateur, ajoutez :

```yaml
name: "Automated Code Review"

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  issues: write
  pull-requests: write

jobs:
  code_review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Run LLM Code Review Action
        uses: jo15122002/flair@v1.0.0  # Ou la référence souhaitée
        with:
          llm-endpoint: ${{ secrets.LLM_ENDPOINT }}
          diff-chunk-size: 10000
          exclude-patterns: "test,tests,spec"
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Suppression des Commentaires

Le projet inclut également des scripts pour supprimer automatiquement les commentaires :

- **delete_pr_comments.py :**  
  Supprime tous les commentaires de la PR.

- **delete_workflow_comments.py :**  
  Supprime les commentaires générés par le workflow (filtrés par un marqueur spécifique).

Vous pouvez créer un workflow manuel (`workflow_dispatch`) pour exécuter ces scripts.

Exemple d'un workflow pour supprimer les commentaires (fichier `.github/workflows/cleanup_comments.yml`) :

```yaml
name: "Cleanup PR Comments"

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "Numéro de la pull request à nettoyer"
        required: true

jobs:
  delete-pr-comments:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.8"

      - name: Install Dependencies
        run: pip install requests

      - name: Delete PR Comments
        env:
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.inputs.pr_number }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python delete_pr_comments.py

  delete-workflow-comments:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.8"

      - name: Install Dependencies
        run: pip install requests

      - name: Delete Workflow Comments
        env:
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.inputs.pr_number }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python delete_workflow_comments.py
```

---

## Contribuer

Les contributions sont les bienvenues !  
- **Forkez le dépôt**
- **Créez une branche pour votre fonctionnalité ou correction**
- **Soumettez un Pull Request**

---

## Licence

Ce projet est sous licence [MIT](LICENSE).

---