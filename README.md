# Application agentique de gestion des notes de frais

## Objectif

Cette application permet à un salarié d'importer une photo de note de frais. Un modèle de vision extrait les champs utiles, l'utilisateur peut corriger les valeurs dans un formulaire, puis les données sont envoyées dans un Google Sheet partagé avec le service comptabilité. L'image est aussi uploadée dans Google Drive pour archivage.

## Lien avec le cours sur les CNN

Dans le cours, un réseau neuronal convolutif est présenté comme un modèle adapté à la vision par ordinateur. Les couches de convolution extraient des caractéristiques d'une image, le pooling réduit la taille des représentations, et l'entraînement ajuste les poids à l'aide d'une fonction de coût et d'un optimiseur.

Dans ce TP, on ne réentraîne pas un CNN depuis zéro. On utilise un modèle de vision déjà entraîné via Groq. Cela correspond à l'idée de transfert learning du cours : on s'appuie sur un modèle pré-entraîné capable de comprendre des images, puis on lui demande une tâche métier précise : extraire les informations d'une note de frais dans un JSON structuré.

## Structure du projet

```text
expense-tracker/
├── backend.py              # Agent IA ExpenseAgent avec Groq Vision
├── app.py                  # Serveur FastAPI et routes HTMX
├── sheets.py               # Client Google Sheets + Drive
├── context.txt             # Prompt système
├── prompt.txt              # Prompt utilisateur
├── requirements.txt
├── .env.example
├── .gitignore
├── test_sheets.py          # Test isolé Google Sheets
├── test_images/            # Images locales de test, ignorées par Git
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## Installation locale sur Windows PowerShell

```powershell
cd C:\Imen\alternance
mkdir expense-tracker
cd expense-tracker

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env
notepad .env
```

## Configuration Google Cloud

1. Ouvrir Google Cloud Console.
2. Créer un projet, par exemple `expense-tracker-tp`.
3. Activer les API suivantes :
   - Google Sheets API
   - Google Drive API
4. Créer un compte de service.
5. Télécharger la clé JSON du compte de service.
6. Placer le fichier JSON dans un dossier local non commité, par exemple :

```text
C:/Imen/alternance/expense-tracker/credentials/expense-agent.json
```

7. Dans Google Sheets, créer un Sheet avec une feuille nommée exactement :

```text
Notes de frais
```

8. Ajouter les en-têtes de colonnes dans cet ordre :

```text
Horodatage | Type | Fournisseur | Date | Montant TTC (€) | TVA (€) | Devise | Description | Confiance | Image
```

9. Partager le Sheet avec l'adresse e-mail du compte de service en rôle Éditeur.
10. Copier l'ID du Sheet depuis l'URL.

## Exemple de fichier `.env`

```env
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxx"
GOOGLE_SHEET_ID="1AbCDefGhiJKlmNoPqRstuVWxyz123456789"
GOOGLE_SERVICE_ACCOUNT_JSON="C:/Imen/alternance/expense-tracker/credentials/expense-agent.json"
GOOGLE_DRIVE_FOLDER_ID=""
GROQ_MODEL="meta-llama/llama-4-scout-17b-16e-instruct"
```

Ne jamais commiter `.env` ni le fichier JSON du compte de service.

## Test 1 : tester Google Sheets seul

```powershell
python test_sheets.py
```

Résultat attendu : une ligne de test apparaît dans le Google Sheet.

## Test 2 : tester l'extraction IA seule

Place une image de ticket dans `test_images`, par exemple :

```text
test_images/ticket.jpg
```

Puis lance :

```powershell
python backend.py test_images/ticket.jpg
```

Résultat attendu : un JSON avec les champs extraits.

Exemple :

```json
{
  "type_document": "restaurant",
  "fournisseur": "Bistrot Paul",
  "date": "22/05/2026",
  "montant_ttc": 18.9,
  "tva": 1.72,
  "devise": "EUR",
  "description": "Repas professionnel",
  "confiance": "haute"
}
```

## Lancement de l'application web

```powershell
uvicorn app:app --reload
```

Puis ouvrir :

```text
http://127.0.0.1:8000
```

## Scénarios à tester

| Scénario | Résultat attendu |
|---|---|
| Ticket de restaurant lisible | Tous les champs sont extraits, confiance haute |
| Billet SNCF | Fournisseur = SNCF, type = transport |
| Photo floue | Confiance basse, certains champs peuvent être vides |
| Mauvais format | Message d'erreur clair |
| Correction manuelle | Le Sheet reçoit la valeur corrigée |
| Soumission sans image | Le Sheet reçoit une ligne sans URL d'image |

## Git conseillé

```powershell
git init
git add .
git commit -m "feature: initialisation du projet notes de frais"

git checkout -b feature/extraction-backend
git add backend.py context.txt prompt.txt requirements.txt
git commit -m "feature: extraction IA des notes de frais"

git checkout main
git merge feature/extraction-backend

git checkout -b feature/google-sheets
git add sheets.py test_sheets.py requirements.txt
git commit -m "feature: integration google sheets et drive"

git checkout main
git merge feature/google-sheets

git checkout -b feature/frontend-vibe
git add app.py static/
git commit -m "feature: interface htmx pour notes de frais"

git checkout main
git merge feature/frontend-vibe
```

## Points importants pour la notation

- Extraction IA avec les 8 champs demandés.
- Formulaire éditable avant soumission.
- Envoi dans Google Sheets.
- Upload de l'image dans Drive avec lien dans le Sheet.
- Gestion d'erreurs côté backend et côté HTMX.
- README clair et dépôt Git propre.
- `.env` et credentials JSON non committés.
