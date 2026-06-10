import base64
import html
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import ExpenseAgent
from sheets import GoogleSheetsClient

BASE_DIR = Path(__file__).resolve().parent
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo
ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic"}

app = FastAPI(title="Expense Tracker Agentique")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_expense_agent: Optional[ExpenseAgent] = None
_sheets_client: Optional[GoogleSheetsClient] = None


def get_agent() -> ExpenseAgent:
    global _expense_agent
    if _expense_agent is None:
        _expense_agent = ExpenseAgent()
    return _expense_agent


def get_sheets_client() -> GoogleSheetsClient:
    global _sheets_client
    if _sheets_client is None:
        _sheets_client = GoogleSheetsClient()
    return _sheets_client


def e(value) -> str:
    """Échappe les valeurs injectées dans le HTML."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def selected(current_value: str, expected_value: str) -> str:
    return "selected" if str(current_value) == expected_value else ""


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/api/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Aucun fichier reçu.")

    media_type = file.content_type or ""
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilise une image JPG, PNG, WEBP ou HEIC.",
        )

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Le fichier image est vide.")
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image trop lourde : maximum 5 Mo.")

    try:
        data = get_agent().extract_from_bytes(image_bytes, media_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur pendant l'analyse IA : {exc}")

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return HTMLResponse(render_edit_form(data, image_base64, media_type))


@app.post("/api/submit", response_class=HTMLResponse)
async def submit_expense(
    type_document: str = Form("autre"),
    fournisseur: str = Form(""),
    date: str = Form(""),
    montant_ttc: str = Form(""),
    tva: str = Form(""),
    devise: str = Form("EUR"),
    description: str = Form(""),
    confiance: str = Form("basse"),
    image_data: str = Form(""),
    image_media_type: str = Form("image/jpeg"),
):
    data = {
        "type_document": type_document,
        "fournisseur": fournisseur,
        "date": date,
        "montant_ttc": to_float_or_none(montant_ttc),
        "tva": to_float_or_none(tva),
        "devise": devise or "EUR",
        "description": description,
        "confiance": confiance,
    }

    try:
        image_url = ""
        if image_data.strip():
            image_bytes = base64.b64decode(image_data)
            image_url = get_sheets_client().upload_image(
                image_bytes=image_bytes,
                media_type=image_media_type,
            )

        get_sheets_client().append_expense(data, image_url=image_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur pendant l'envoi vers Google Sheets : {exc}")

    return HTMLResponse(
        f"""
        <div class="alert alert-success">
            <strong>Note de frais envoyée avec succès.</strong><br>
            Fournisseur : {e(fournisseur) or "non renseigné"} · Montant TTC : {e(montant_ttc) or "non renseigné"} {e(devise or "EUR")}
            {f'<br><a href="{e(image_url)}" target="_blank" rel="noopener">Voir l’image archivée</a>' if image_url else ''}
        </div>
        """
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        render_error(str(exc.detail)),
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return HTMLResponse(
        render_error(f"Erreur inattendue : {exc}"),
        status_code=500,
    )


def to_float_or_none(value: str):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", ".").replace("€", "").strip())
    except ValueError:
        return None


def render_error(message: str) -> str:
    return f"""
    <div class="alert alert-error">
        <strong>Erreur</strong><br>
        {e(message)}
    </div>
    """


def render_edit_form(data: dict, image_base64: str, media_type: str) -> str:
    type_document = data.get("type_document") or "autre"
    confiance = data.get("confiance") or "basse"

    return f"""
    <section class="card result-card">
        <div class="section-title">
            <span>2</span>
            <div>
                <h2>Vérifier et corriger les champs</h2>
                <p>L'IA a pré-rempli le formulaire. Tu peux modifier avant l'envoi.</p>
            </div>
        </div>

        <form
            id="expense-form"
            class="expense-form"
            hx-post="/api/submit"
            hx-target="#confirmation-container"
            hx-swap="innerHTML"
        >
            <input type="hidden" name="image_data" value="{e(image_base64)}">
            <input type="hidden" name="image_media_type" value="{e(media_type)}">

            <label>
                Type de document
                <select name="type_document" required>
                    <option value="restaurant" {selected(type_document, "restaurant")}>Restaurant</option>
                    <option value="transport" {selected(type_document, "transport")}>Transport</option>
                    <option value="hôtel" {selected(type_document, "hôtel")}>Hôtel</option>
                    <option value="autre" {selected(type_document, "autre")}>Autre</option>
                </select>
            </label>

            <label>
                Fournisseur
                <input type="text" name="fournisseur" value="{e(data.get('fournisseur'))}" placeholder="Ex : SNCF, Ibis, Bistrot Paul">
            </label>

            <label>
                Date
                <input type="text" name="date" value="{e(data.get('date'))}" placeholder="JJ/MM/AAAA">
            </label>

            <div class="grid-2">
                <label>
                    Montant TTC (€)
                    <input type="number" step="0.01" name="montant_ttc" value="{e(data.get('montant_ttc'))}" placeholder="0.00">
                </label>

                <label>
                    TVA (€)
                    <input type="number" step="0.01" name="tva" value="{e(data.get('tva'))}" placeholder="0.00">
                </label>
            </div>

            <div class="grid-2">
                <label>
                    Devise
                    <input type="text" name="devise" value="{e(data.get('devise') or 'EUR')}" maxlength="3">
                </label>

                <label>
                    Confiance
                    <select name="confiance" required>
                        <option value="haute" {selected(confiance, "haute")}>Haute</option>
                        <option value="moyen" {selected(confiance, "moyen")}>Moyen</option>
                        <option value="basse" {selected(confiance, "basse")}>Basse</option>
                    </select>
                </label>
            </div>

            <label>
                Description
                <textarea name="description" rows="3" placeholder="Motif de la dépense">{e(data.get('description'))}</textarea>
            </label>

            <div class="actions">
                <button type="submit" class="primary-button">Envoyer vers le Google Sheet</button>
                <button type="button" class="secondary-button" id="reset-button-inline">Recommencer</button>
            </div>
        </form>

        <div id="confirmation-container"></div>
    </section>
    """
