import io
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

BASE_DIR = Path(__file__).resolve().parent

WORKSHEET_NAME = "Notes de frais"

HEADERS = [
    "Horodatage",
    "Type",
    "Fournisseur",
    "Date",
    "Montant TTC (€)",
    "TVA (€)",
    "Devise",
    "Description",
    "Confiance",
    "Image",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsClient:
    """
    Cette classe gère :
    - la connexion au Google Sheet
    - l'ajout d'une ligne de note de frais
    - l'upload de l'image dans Google Drive
    """

    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")

        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID") or None

        if not sheet_id:
            raise RuntimeError("GOOGLE_SHEET_ID est manquant dans le fichier .env")

        if not credentials_path:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON est manquant dans le fichier .env"
            )

        path = Path(credentials_path)

        if not path.is_absolute():
            path = BASE_DIR / path

        if not path.exists():
            raise FileNotFoundError(f"Fichier credentials introuvable : {path}")

        self.credentials = Credentials.from_service_account_file(
            str(path),
            scopes=SCOPES
        )

        self.gc = gspread.authorize(self.credentials)
        self.spreadsheet = self.gc.open_by_key(sheet_id)
        self.worksheet = self._get_or_create_worksheet()

        self.drive_service = build(
            "drive",
            "v3",
            credentials=self.credentials
        )

    def _get_or_create_worksheet(self):
        """
        Récupère la feuille 'Notes de frais'.
        Si elle n'existe pas, elle est créée automatiquement.
        """

        try:
            worksheet = self.spreadsheet.worksheet(WORKSHEET_NAME)

        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=WORKSHEET_NAME,
                rows=1000,
                cols=len(HEADERS)
            )

            worksheet.append_row(
                HEADERS,
                value_input_option="USER_ENTERED"
            )

            return worksheet

        first_row = worksheet.row_values(1)

        if not first_row:
            worksheet.append_row(
                HEADERS,
                value_input_option="USER_ENTERED"
            )

        return worksheet

    def append_expense(
        self,
        data: Dict[str, Any],
        image_url: Optional[str] = None
    ) -> None:
        """
        Ajoute une ligne dans le Google Sheet.
        """

        row = [
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            data.get("type_document") or "",
            data.get("fournisseur") or "",
            data.get("date") or "",
            self._number_or_empty(data.get("montant_ttc")),
            self._number_or_empty(data.get("tva")),
            data.get("devise") or "EUR",
            data.get("description") or "",
            data.get("confiance") or "",
            image_url or "",
        ]

        self.worksheet.append_row(
            row,
            value_input_option="USER_ENTERED"
        )

    def upload_image(
        self,
        image_bytes: bytes,
        media_type: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload l'image dans Google Drive.
        Rend le fichier lisible publiquement.
        Retourne l'URL Drive.
        """

        if not image_bytes:
            return ""

        extension = self._extension_from_media_type(media_type)

        final_filename = filename or (
            f"note-frais-{datetime.now().strftime('%Y%m%d-%H%M%S')}{extension}"
        )

        metadata = {
            "name": final_filename
        }

        if self.drive_folder_id:
            metadata["parents"] = [self.drive_folder_id]

        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes),
            mimetype=media_type,
            resumable=False
        )

        created_file = (
            self.drive_service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id, webViewLink"
            )
            .execute()
        )

        file_id = created_file["id"]

        self.drive_service.permissions().create(
            fileId=file_id,
            body={
                "type": "anyone",
                "role": "reader"
            },
            fields="id",
        ).execute()

        return f"https://drive.google.com/file/d/{file_id}/view"

    def _number_or_empty(self, value: Any) -> Any:
        """
        Convertit les montants en nombres.
        Si la valeur est vide ou invalide, retourne une cellule vide.
        """

        if value is None or value == "":
            return ""

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(
                str(value)
                .replace(",", ".")
                .replace("€", "")
                .strip()
            )

        except ValueError:
            return ""

    def _extension_from_media_type(self, media_type: str) -> str:
        mapping = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/heic": ".heic",
        }

        return mapping.get(media_type, ".jpg")
