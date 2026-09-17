from __future__ import annotations

import locale

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Watermark Remover Pro", "subtitle": "Restore media you own or are authorized to edit",
        "open": "Add files", "clear": "Clear list", "remove": "Remove selected",
        "preview": "Select areas", "preview_result": "Preview result", "process": "Process", "cancel": "Cancel",
        "output": "Output folder", "browse": "Browse", "areas": "Areas", "save_areas": "Save areas",
        "load_areas": "Load areas", "clear_areas": "Clear areas", "areas_loaded": "Area preset loaded",
        "areas_cleared": "Custom areas cleared", "preset_invalid": "This area preset is invalid.",
        "corners": "Automatic corner areas", "top_left": "Top left", "top_right": "Top right",
        "bottom_left": "Bottom left", "bottom_right": "Bottom right", "method": "Inpainting",
        "restore_tab": "Restoration", "performance_tab": "Video / performance",
        "mixed": "Adaptive", "telea": "Telea", "ns": "Navier–Stokes", "radius": "Radius",
        "margin": "Mask margin", "feather": "Feather", "smoothing": "Repair smoothing",
        "denoise": "Denoise", "sharpen": "Sharpen", "color": "Auto color correction",
        "audio": "Preserve video audio", "quality": "Image output quality", "codec": "Video codec",
        "workers": "Frame workers", "hardware": "Try hardware video decode", "buffering": "Buffer processed frames",
        "mp4v": "MP4V (compatible)", "h264": "H.264 (if available)", "xvid": "XVID / AVI",
        "fast": "Fast", "balanced": "Balanced", "high": "High", "status_ready": "Ready",
        "status_processing": "Processing", "status_done": "Finished", "status_cancelled": "Cancelled",
        "select_output": "Select output folder", "no_files": "Add at least one image or video first.",
        "no_output": "Select an output folder first.", "no_areas": "Select a custom area or enable at least one corner.",
        "select_areas_hint": "Draw one or more rectangles, then press Enter/Space to accept or Esc to cancel.",
        "area_saved": "Custom areas saved", "language": "Language", "logs": "Activity log",
        "file": "File", "type": "Type", "state": "State", "pending": "Pending", "done": "Done",
        "failed": "Failed", "cancelled": "Cancelled", "about": "by Swir",
        "notice": "Use only on media you own or have permission to modify.",
    },
    "pl": {
        "title": "Watermark Remover Pro", "subtitle": "Odnawiaj multimedia, które posiadasz lub możesz legalnie edytować",
        "open": "Dodaj pliki", "clear": "Wyczyść listę", "remove": "Usuń zaznaczone",
        "preview": "Wybierz obszary", "preview_result": "Podgląd efektu", "process": "Przetwarzaj", "cancel": "Anuluj",
        "output": "Folder wyjściowy", "browse": "Wybierz", "areas": "Obszary", "save_areas": "Zapisz obszary",
        "load_areas": "Wczytaj obszary", "clear_areas": "Wyczyść obszary", "areas_loaded": "Wczytano preset obszarów",
        "areas_cleared": "Wyczyszczono własne obszary", "preset_invalid": "Preset obszarów jest nieprawidłowy.",
        "corners": "Automatyczne obszary rogów", "top_left": "Lewy górny", "top_right": "Prawy górny",
        "bottom_left": "Lewy dolny", "bottom_right": "Prawy dolny", "method": "Wypełnianie",
        "restore_tab": "Odnawianie", "performance_tab": "Wideo / wydajność",
        "mixed": "Adaptacyjne", "telea": "Telea", "ns": "Navier–Stokes", "radius": "Promień",
        "margin": "Margines maski", "feather": "Wygładzanie krawędzi", "smoothing": "Wygładzanie naprawy",
        "denoise": "Redukcja szumu", "sharpen": "Wyostrzanie", "color": "Automatyczna korekcja kolorów",
        "audio": "Zachowaj dźwięk wideo", "quality": "Jakość zapisu obrazów", "codec": "Kodek wideo",
        "workers": "Wątki klatek", "hardware": "Spróbuj sprzętowego dekodowania", "buffering": "Buforuj przetworzone klatki",
        "mp4v": "MP4V (zgodny)", "h264": "H.264 (jeśli dostępny)", "xvid": "XVID / AVI",
        "fast": "Szybka", "balanced": "Zbalansowana", "high": "Wysoka",
        "status_ready": "Gotowy", "status_processing": "Przetwarzanie", "status_done": "Zakończono",
        "status_cancelled": "Anulowano", "select_output": "Wybierz folder wyjściowy",
        "no_files": "Najpierw dodaj co najmniej jeden obraz lub film.", "no_output": "Najpierw wybierz folder wyjściowy.",
        "no_areas": "Wybierz własny obszar lub zaznacz co najmniej jeden róg.",
        "select_areas_hint": "Narysuj jeden lub więcej prostokątów, potem Enter/Spacja zatwierdza, Esc anuluje.",
        "area_saved": "Zapisano własne obszary", "language": "Język", "logs": "Dziennik aktywności",
        "file": "Plik", "type": "Typ", "state": "Stan", "pending": "Oczekuje", "done": "Gotowe",
        "failed": "Błąd", "cancelled": "Anulowano", "about": "by Swir",
        "notice": "Używaj wyłącznie na materiałach, które posiadasz lub masz prawo modyfikować.",
    },
}


def detect_language() -> str:
    try:
        lang = locale.getlocale()[0] or ""
    except Exception:
        lang = ""
    return "pl" if str(lang).lower().startswith("pl") else "en"


def text(language: str, key: str) -> str:
    return STRINGS.get(language, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
