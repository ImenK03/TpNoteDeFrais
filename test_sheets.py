from sheets import GoogleSheetsClient

if __name__ == "__main__":
    client = GoogleSheetsClient()
    client.append_expense(
        {
            "type_document": "restaurant",
            "fournisseur": "Test Bistrot",
            "date": "01/06/2026",
            "montant_ttc": 18.90,
            "tva": 1.72,
            "devise": "EUR",
            "description": "Ligne de test générée par test_sheets.py",
            "confiance": "haute",
        },
        image_url=None,
    )
    print("OK : ligne de test ajoutée dans Google Sheets.")
