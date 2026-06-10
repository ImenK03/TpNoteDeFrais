import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent

EXPECTED_FIELDS = [
    "type_document",
    "fournisseur",
    "date",
    "montant_ttc",
    "tva",
    "devise",
    "description",
    "confiance",
]

ALLOWED_TYPES = {"restaurant", "transport", "hôtel", "hotel", "autre"}
ALLOWED_CONFIDENCE = {"haute", "moyen", "basse"}


class ExpenseAgent:
    """
    Agent IA chargé d'extraire les champs d'une note de frais depuis une image.

    Lien avec le cours du professeur :
    les CNN permettent d'extraire des caractéristiques visuelles depuis une image.
    Ici, on n'entraîne pas un CNN depuis zéro : on utilise un modèle de vision
    pré-entraîné via Groq pour réaliser une extraction métier.
    """

    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY est manquante dans le fichier .env")

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        )

        self.context = self._read_text_file("context.txt")
        self.prompt = self._read_text_file("prompt.txt")

    def _read_text_file(self, filename: str) -> str:
        path = BASE_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path}")

        return path.read_text(encoding="utf-8")

    def extract_from_bytes(self, image_bytes: bytes, media_type: str) -> Dict[str, Any]:
        """
        Encode l'image en base64, appelle le modèle de vision,
        parse le JSON retourné et renvoie un dictionnaire Python propre.
        """

        if not image_bytes:
            raise ValueError("L'image est vide.")

        if not media_type or not media_type.startswith("image/"):
            raise ValueError("Le fichier fourni n'est pas une image valide.")

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{media_type};base64,{encoded_image}"

        messages = [
            {
                "role": "system",
                "content": self.context
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    }
                ]
            }
        ]

        request_payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 1024
        }

        try:
            completion = self.client.chat.completions.create(**request_payload)
        except TypeError:
            request_payload["max_tokens"] = request_payload.pop("max_completion_tokens")
            completion = self.client.chat.completions.create(**request_payload)

        raw_content = completion.choices[0].message.content
        parsed = self._parse_json(raw_content)

        return self._normalize_result(parsed)

    def _parse_json(self, raw_content: Optional[str]) -> Dict[str, Any]:
        if not raw_content:
            raise ValueError("Le modèle n'a retourné aucun contenu.")

        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            start = raw_content.find("{")
            end = raw_content.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise ValueError("La réponse du modèle n'est pas un JSON valide.")

            return json.loads(raw_content[start:end + 1])

    def _normalize_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sécurise les données retournées par le modèle.
        Le modèle peut oublier un champ, retourner null ou mal formater un nombre.
        """

        normalized: Dict[str, Any] = {
            field: data.get(field, None)
            for field in EXPECTED_FIELDS
        }

        type_document = normalized.get("type_document")

        if isinstance(type_document, str):
            type_document = type_document.strip().lower()

            if type_document == "hotel":
                type_document = "hôtel"

            normalized["type_document"] = (
                type_document if type_document in ALLOWED_TYPES else "autre"
            )
        else:
            normalized["type_document"] = "autre"

        confiance = normalized.get("confiance")

        if isinstance(confiance, str):
            confiance = confiance.strip().lower()
            normalized["confiance"] = (
                confiance if confiance in ALLOWED_CONFIDENCE else "basse"
            )
        else:
            normalized["confiance"] = "basse"

        normalized["montant_ttc"] = self._to_float_or_none(
            normalized.get("montant_ttc")
        )

        normalized["tva"] = self._to_float_or_none(
            normalized.get("tva")
        )

        devise = normalized.get("devise")

        if devise is None or str(devise).strip() == "":
            normalized["devise"] = "EUR"
        else:
            normalized["devise"] = str(devise).strip().upper()

        for key in ["fournisseur", "date", "description"]:
            value = normalized.get(key)

            if value is not None:
                value = str(value).strip()
                normalized[key] = value if value else None

        return normalized

    def _to_float_or_none(self, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None

        if isinstance(value, (int, float)):
            return float(value)

        try:
            cleaned = (
                str(value)
                .replace("€", "")
                .replace(",", ".")
                .strip()
            )

            return float(cleaned)

        except ValueError:
            return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tester l'extraction d'une note de frais en ligne de commande"
    )

    parser.add_argument(
        "image_path",
        help="Chemin vers une image de ticket ou de facture"
    )

    args = parser.parse_args()

    image_path = Path(args.image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image introuvable : {image_path}")

    media_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"

    agent = ExpenseAgent()

    result = agent.extract_from_bytes(
        image_path.read_bytes(),
        media_type
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
