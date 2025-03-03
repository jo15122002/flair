# LLM Code Review & Comment Management

Ce projet est conçu pour automatiser la revue de code et la gestion des commentaires sur les *pull requests* en utilisant un modèle LLM. Il intègre des workflows GitHub Actions pour :

- Exécuter des tests unitaires.
- Récupérer et filtrer les diff entre branches.
- Interroger un serveur LLM pour obtenir des commentaires sur le code.
- Publier les commentaires sur une *pull request* via l'API de GitHub.
- Nettoyer les commentaires générés par le workflow.

## Structure du Projet

- **Configuration et Variables d'Environnement** :  
  - [`.env.example`](.env.example) – Exemple de configuration des variables d'environnement.
  - [src/config.py](src/config.py) – Chargement et définition de la configuration du projet.

- **Actions et Workflows GitHub** :  
  - [`.github/workflows/cleanup_comment.yml`](.github/workflows/cleanup_comment.yml) – Workflow pour supprimer les commentaires sur la PR.
  - [`.github/workflows/llm_code_review.yml`](.github/workflows/llm_code_review.yml) – Workflow pour lancer la revue de code automatisée.
  - [action.yml](action.yml) – Définition de l'action GitHub pour la revue de code.
  - [action_usage.yml.example](action_usage.yml.example) – Exemple d'utilisation de l'action.

- **Code Principal et Modules** :  
  - [src/main.py](src/main.py) – Point d'entrée du script de revue de code automatisée.
  - [src/diff_extractor.py](src/diff_extractor.py) – Extraction et découpage du diff pour chaque *pull request*.
  - [src/llm_client.py](src/llm_client.py) – Communication avec le serveur LLM et traitement de la réponse.
  - [src/comment_publisher.py](src/comment_publisher.py) et [src/comment_publisher_github.py](src/comment_publisher_github.py) – Publication des commentaires sur GitHub.
  - [src/delete_pr_comments.py](src/delete_pr_comments.py) et [src/delete_workflow_comments.py](src/delete_workflow_comments.py) – Supprimer les commentaires de la PR.

- **Tests** :  
  - [tests/test_diff_extractor.py](tests/test_diff_extractor.py)  
  - [tests/test_llm_client.py](tests/test_llm_client.py)  
  - [tests/test_comment_publisher_github.py](tests/test_comment_publisher_github.py)

```
  Directory structure:
  └── jo15122002-flair/
    ├── readme.md
    ├── LICENSE
    ├── action.yml
    ├── action_usage.yml.example
    ├── requirements.txt
    ├── .env.example
    ├── src/
    │   ├── __init__.py
    │   ├── comment_publisher.py
    │   ├── comment_publisher_github.py
    │   ├── config.py
    │   ├── delete_pr_comments.py
    │   ├── delete_workflow_comments.py
    │   ├── diff_extractor.py
    │   ├── llm_client.py
    │   ├── main.py
    │   └── utils.py
    ├── tests/
    │   ├── __init__.py
    │   ├── test_comment_publisher.py
    │   ├── test_comment_publisher_github.py
    │   ├── test_diff_extractor.py
    │   └── test_llm_client.py
    └── .github/
        └── workflows/
            ├── cleanup_comment.yml
            └── llm_code_review.yml
```

## Prérequis

- Python 3.8 ou supérieur.
- Dépendances installées via le fichier [requirements.txt](requirements.txt) :
  ```sh
  pip install -r requirements.txt
  ```

## Utilisation

1. **Configuration**  
   Créez un fichier .env en vous basant sur .env.example et complétez les variables nécessaires (notamment les tokens et URL).

2. **Lancement en Local**  
   Exécutez le script principal pour traiter une *pull request* :
   ```sh
   python src/main.py
   ```

3. **Tests**  
   Pour lancer les tests unitaires avec `pytest` :
   ```sh
   pytest
   ```

4. **Intégration avec GitHub Actions**  
   Configurez vos workflows en fonction des fichiers présents dans le répertoire workflows. Ils permettent notamment de :
   - Lancer la revue de code automatisée à l'ouverture ou la mise à jour d'une *pull request*.
   - Nettoyer automatiquement les commentaires de revue de code précédents.

## Déploiement

Ce projet est prêt à être utilisé en tant qu'action GitHub. Pour l'utiliser dans un autre dépôt, référez-vous à l'exemple dans action_usage.yml.example.

## Licence

Ce projet est distribué sous licence Apache 2.0.