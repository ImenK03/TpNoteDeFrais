from sheets import GoogleSheetsClient


def main():
    client = GoogleSheetsClient()

    fake_expense = {
        "type_document": "restaurant",
        "fournisseur": "Test Restaurant",
        "date": "22/05/2026",
        "montant_ttc": 19.90,
        "tva": 1.81,
        "devise": "EUR",
        "description": "Ligne de test ajoutée depuis test_sheets.py",
        "confiance": "haute",
    }

    client.append_expense(
        fake_expense,
        image_url="https://example.com/image-test.jpg"
    )

    print("Ligne de test ajoutée dans Google Sheets.")


if __name__ == "__main__":
    main()
