from __future__ import annotations

import locale

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Watermark Remover Pro", "subtitle": "Restore media you own or are authorized to edit",
        "open": "Add files", "clear": "Clear list", "remove": "Remove selected",
        "preview": "Preview / select areas", "process": "Process", "cancel": "Cancel",
        "output": "Output folder", "browse": "Browse", "areas": "Areas",
        "corners": "Automatic corner areas", "top_left": "Top left", "top_right": "Top right",
        "bottom_left": "Bottom left", "bottom_right": "Bottom right", "method": "Inpainting",
        "mixed": "Adaptive", "telea": "Telea", "ns": "Navier–Stokes", "radius": "Radius",
        "margin": "Mask margin", "feather": "Feather", "denoise": "Denoise", "sharpen": "Sharpen",
        "color": "Auto color correction", "audio": "Preserve video audio", "quality": "Quality",
        "fast": "Fast", "balanced": "Balanced", "high": "High", "status_ready": "Ready",
        "status_processing": "Processing", "status_done": "Finished", "status_cancelled": "Cancelled",
        "select_output": "Select output folder", "no_files": "Add at least one image or video first.",
        "no_output": "Select an output folder first.",
        "select_areas_hint": "Drag rectangles over the areas to restore. Right-click removes the last area. Enter saves; Esc cancels.",
        "area_saved": "Custom areas saved", "language": "Language", "logs": "Activity log",
        "file": "File", "type": "Type", "state": "State", "pending": "Pending", "done": "Done",
        "failed": "Failed", "cancelled": "Cancelled", "about": "by Swir",
        "notice": "Use only on media you own or have permission to modify.",
    },
    "pl": {
        "title": "Watermark Remover Pro", "subtitle": "Odnawiaj multimedia, które posiadasz lub możesz legalnie edytować",
        "open": "Dodaj pliki", "clear": "Wyczyść listę", "remove": "Usuń zaznaczone",
        "preview": "Podgląd / wybór obszarów", "process": "Przetwarzaj", "cancel": "Anuluj",
        "output": "Folder wyjściowy", "browse": "Wybierz", "areas": "Obszary",
        "corners": "Automatyczne obszary rogów", "top_left": "Lewy górny", "top_right": "Prawy górny",
        "bottom_left": "Lewy dolny", "bottom_right": "Prawy dolny", "method": "Wypełnianie",
        "mixed": "Adaptacyjne", "telea": "Telea", "ns": "Navier–Stokes", "radius": "Promień",
        "margin": "Margines maski", "feather": "Wygładzanie krawędzi", "denoise": "Redukcja szumu",
        "sharpen": "Wyostrzanie", "color": "Automatyczna korekcja kolorów", "audio": "Zachowaj dźwięk wideo",
        "quality": "Jakość", "fast": "Szybka", "balanced": "Zbalansowana", "high": "Wysoka",
        "status_ready": "Gotowy", "status_processing": "Przetwarzanie", "status_done": "Zakończono",
        "status_cancelled": "Anulowano", "select_output": "Wybierz folder wyjściowy",
        "no_files": "Najpierw dodaj co najmniej jeden obraz lub film.", "no_output": "Najpierw wybierz folder wyjściowy.",
        "select_areas_hint": "Przeciągnij prostokąty nad obszarami do odtworzenia. Prawy przycisk usuwa ostatni. Enter zapisuje; Esc anuluje.",
        "area_saved": "Zapisano własne obszary", "language": "Język", "logs": "Dziennik aktywności",
        "file": "Plik", "type": "Typ", "state": "Stan", "pending": "Oczekuje", "done": "Gotowe",
        "failed": "Błąd", "cancelled": "Anulowano", "about": "by Swir",
        "notice": "Używaj wyłącznie na materiałach, które posiadasz lub masz prawo modyfikować.",
    },
}


def detect_language() -> str:
    try:
        lang = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except Exception:
        lang = ""
    return "pl" if str(lang).lower().startswith("pl") else "en"


def text(language: str, key: str) -> str:
    return STRINGS.get(language, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
