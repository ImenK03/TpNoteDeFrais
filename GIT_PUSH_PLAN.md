# Plan de push GitHub naturel pour le projet `expense-tracker`

Ce fichier sert de guide pour rendre un historique Git crédible et propre. L'idée est de ne pas tout pousser d'un seul coup, mais de faire plusieurs commits/pushs correspondant aux grandes étapes du TP.

## Avant de commencer

Dans PowerShell :

```powershell
cd C:\Imen\alternance\expense-tracker
```

Vérifie que les fichiers sensibles ne seront pas envoyés :

```powershell
git status --ignored
```

À ne jamais commiter :

```text
.env
credentials/
*.json
.venv/
__pycache__/
```

## Connexion au repo GitHub

Crée d'abord un repository vide sur GitHub, par exemple :

```text
expense-tracker
```

Puis dans PowerShell :

```powershell
git init
git branch -M main
git remote add origin https://github.com/TON_PSEUDO/expense-tracker.git
```

Remplace `TON_PSEUDO` par ton identifiant GitHub.

---

# Push 1 — Mise en place du projet

À faire quand tu as créé la structure du dossier et les fichiers de configuration.

```powershell
git add .gitignore .env.example requirements.txt test_images/.gitkeep
git commit -m "feature: initialise la structure du projet"
git push -u origin main
```

Ce push montre que tu as commencé proprement avec l'environnement Python, les dépendances et la protection des credentials.

---

# Push 2 — Prompts IA

À faire quand tu as rédigé le contexte système et le prompt utilisateur.

```powershell
git checkout -b feature/prompts-ia
git add context.txt prompt.txt
git commit -m "feature: ajoute les prompts pour l'extraction des notes de frais"
git push -u origin feature/prompts-ia
```

Puis fusion dans `main` :

```powershell
git checkout main
git merge feature/prompts-ia
git push origin main
```

---

# Push 3 — Backend d'extraction IA

À faire quand `backend.py` fonctionne en ligne de commande avec une image locale.

Test avant commit :

```powershell
python backend.py test_images/ticket.jpg
```

Puis :

```powershell
git checkout -b feature/extraction-backend
git add backend.py
git commit -m "feature: implemente l'agent d'extraction IA"
git push -u origin feature/extraction-backend
```

Fusion :

```powershell
git checkout main
git merge feature/extraction-backend
git push origin main
```

---

# Push 4 — Intégration Google Sheets et Drive

À faire quand `test_sheets.py` ajoute correctement une ligne dans ton Google Sheet.

Test avant commit :

```powershell
python test_sheets.py
```

Puis :

```powershell
git checkout -b feature/google-sheets
git add sheets.py test_sheets.py
git commit -m "feature: ajoute l'integration google sheets et drive"
git push -u origin feature/google-sheets
```

Fusion :

```powershell
git checkout main
git merge feature/google-sheets
git push origin main
```

---

# Push 5 — Serveur FastAPI

À faire quand les routes `/`, `/api/analyze` et `/api/submit` sont créées.

Test avant commit :

```powershell
uvicorn app:app --reload
```

Puis ouvre :

```text
http://127.0.0.1:8000
```

Si le serveur démarre :

```powershell
git checkout -b feature/fastapi-routes
git add app.py
git commit -m "feature: ajoute les routes fastapi pour analyser et soumettre"
git push -u origin feature/fastapi-routes
```

Fusion :

```powershell
git checkout main
git merge feature/fastapi-routes
git push origin main
```

---

# Push 6 — Frontend HTMX

À faire quand l'interface affiche l'upload, la prévisualisation, le formulaire et les messages de confirmation.

```powershell
git checkout -b feature/frontend-htmx
git add static/index.html static/style.css static/app.js
git commit -m "feature: ajoute l'interface htmx de gestion des notes de frais"
git push -u origin feature/frontend-htmx
```

Fusion :

```powershell
git checkout main
git merge feature/frontend-htmx
git push origin main
```

---

# Push 7 — Documentation finale

À faire à la fin, quand tu as testé l'application de bout en bout.

```powershell
git checkout -b doc/readme-final
git add README.md GIT_PUSH_PLAN.md
git commit -m "doc: ajoute la documentation du projet et le plan git"
git push -u origin doc/readme-final
```

Fusion :

```powershell
git checkout main
git merge doc/readme-final
git push origin main
```

---

# Vérification finale

```powershell
git log --oneline --graph --all
```

Tu dois voir plusieurs commits avec des noms naturels, par exemple :

```text
feature: initialise la structure du projet
feature: ajoute les prompts pour l'extraction des notes de frais
feature: implemente l'agent d'extraction IA
feature: ajoute l'integration google sheets et drive
feature: ajoute les routes fastapi pour analyser et soumettre
feature: ajoute l'interface htmx de gestion des notes de frais
doc: ajoute la documentation du projet et le plan git
```

