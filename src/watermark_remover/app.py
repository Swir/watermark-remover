from __future__ import annotations

import json
import logging
import queue
import sys
import threading
import webbrowser
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk
from ttkbootstrap import Style

from . import __version__
from .engine import process_frame
from .i18n import STRINGS, text
from .models import Area, ProcessingOptions, corner_areas
from .settings import SettingsStore, app_data_dir
from .video import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, first_frame, media_kind, process_media


def _resource_path(relative: str) -> Path:
    frozen = getattr(sys, "_MEIPASS", None)
    root = Path(frozen) if frozen else Path(__file__).resolve().parents[2]
    return root / relative


class WatermarkRemoverApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        Style(theme="darkly")
        self.root.geometry("1240x820")
        self.root.minsize(1020, 700)
        self._set_window_icon()

        self.store = SettingsStore()
        self.settings = self.store.load()
        self.language = str(self.settings.get("language", "en"))
        if self.language not in STRINGS:
            self.language = "en"

        self.files: list[Path] = []
        self.custom_areas = SettingsStore.areas_from(self.settings.get("areas", []))
        self.cancel_event = threading.Event()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.row_ids: dict[Path, str] = {}
        self.preview_window: tk.Toplevel | None = None
        self._preview_images: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage] | None = None

        self._setup_logging()
        self._variables()
        self._build()
        self.root.after(100, self._pump)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _set_window_icon(self) -> None:
        icon = _resource_path("assets/watermark-remover.ico")
        if icon.is_file():
            try:
                self.root.iconbitmap(default=str(icon))
            except tk.TclError:
                logging.debug("Window icon could not be loaded", exc_info=True)

    def _setup_logging(self) -> None:
        log_dir = app_data_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=log_dir / "watermark-remover.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            encoding="utf-8",
        )

    def _variables(self) -> None:
        saved = self.settings.get("last_options", {})
        saved_corners = self.settings.get("corners", {})
        self.output_var = tk.StringVar(value=str(self.settings.get("output_dir", Path.home() / "Videos")))
        self.method_var = tk.StringVar(value=str(saved.get("method", "mixed")))
        self.radius_var = tk.IntVar(value=int(saved.get("radius", 7)))
        self.margin_var = tk.IntVar(value=int(saved.get("margin", 12)))
        self.feather_var = tk.IntVar(value=int(saved.get("feather", 5)))
        self.smoothing_var = tk.IntVar(value=int(saved.get("smoothing", saved.get("blur_strength", 0))))
        self.denoise_var = tk.BooleanVar(value=bool(saved.get("denoise", False)))
        self.sharpen_var = tk.BooleanVar(value=bool(saved.get("sharpen", False)))
        self.color_var = tk.BooleanVar(value=bool(saved.get("color_correction", False)))
        self.audio_var = tk.BooleanVar(value=bool(saved.get("preserve_audio", True)))
        self.quality_var = tk.StringVar(value=str(saved.get("output_quality", "high")))
        self.codec_var = tk.StringVar(value=str(saved.get("video_codec", "mp4v")))
        self.workers_var = tk.IntVar(value=int(saved.get("worker_count", 4)))
        self.hw_var = tk.BooleanVar(value=bool(saved.get("hardware_acceleration", True)))
        self.buffering_var = tk.BooleanVar(value=bool(saved.get("buffering", True)))
        self.corner_vars = {
            name: tk.BooleanVar(value=bool(saved_corners.get(name, name == "bottom_right")))
            for name in ("top_left", "top_right", "bottom_left", "bottom_right")
        }
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var = tk.StringVar(value="")

    def t(self, key: str) -> str:
        return text(self.language, key)

    def _build(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(f"{self.t('title')} {__version__}")

        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text=self.t("title"), font=("Segoe UI", 22, "bold")).pack(side="left")
        lang = ttk.Menubutton(header, text=f"{self.t('language')}: {self.language.upper()}")
        lang.pack(side="right")
        menu = tk.Menu(lang, tearoff=False)
        menu.add_command(label="Polski", command=lambda: self._language("pl"))
        menu.add_command(label="English", command=lambda: self._language("en"))
        lang["menu"] = menu
        ttk.Label(outer, text=self.t("subtitle"), foreground="#8ba3c7").pack(anchor="w", pady=(0, 12))

        pane = ttk.Panedwindow(outer, orient="horizontal")
        pane.pack(fill="both", expand=True)
        left = ttk.Frame(pane, padding=(0, 0, 10, 0))
        right = ttk.Frame(pane, padding=(10, 0, 0, 0))
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text=self.t("open"), command=self._add).pack(side="left", padx=(0, 5))
        ttk.Button(bar, text=self.t("remove"), command=self._remove).pack(side="left", padx=5)
        ttk.Button(bar, text=self.t("clear"), command=self._clear).pack(side="left", padx=5)
        ttk.Button(bar, text=self.t("preview_result"), command=self._preview_result).pack(side="right", padx=(5, 0))
        ttk.Button(bar, text=self.t("preview"), command=self._select_areas).pack(side="right")

        tf = ttk.Frame(left)
        tf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tf, columns=("type", "state"), show="tree headings", selectmode="extended")
        self.tree.heading("#0", text=self.t("file"))
        self.tree.heading("type", text=self.t("type"))
        self.tree.heading("state", text=self.t("state"))
        self.tree.column("#0", width=410, minwidth=220)
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("state", width=115, anchor="center")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        out = ttk.LabelFrame(left, text=self.t("output"), padding=10)
        out.pack(fill="x", pady=(10, 0))
        ttk.Entry(out, textvariable=self.output_var).pack(side="left", fill="x", expand=True)
        ttk.Button(out, text=self.t("browse"), command=self._browse).pack(side="right", padx=(7, 0))

        corners = ttk.LabelFrame(right, text=self.t("corners"), padding=10)
        corners.pack(fill="x")
        for idx, key in enumerate(("top_left", "top_right", "bottom_left", "bottom_right")):
            ttk.Checkbutton(corners, text=self.t(key), variable=self.corner_vars[key]).grid(
                row=idx // 2, column=idx % 2, sticky="w", padx=5, pady=4
            )
        self.area_label = ttk.Label(
            corners, text=f"{self.t('areas')}: {len(self.custom_areas)}", foreground="#8ba3c7"
        )
        self.area_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 4))
        preset_bar = ttk.Frame(corners)
        preset_bar.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(preset_bar, text=self.t("save_areas"), command=self._save_area_preset).pack(side="left", padx=(0, 4))
        ttk.Button(preset_bar, text=self.t("load_areas"), command=self._load_area_preset).pack(side="left", padx=4)
        ttk.Button(preset_bar, text=self.t("clear_areas"), command=self._clear_areas).pack(side="left", padx=4)

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True, pady=(10, 0))
        restore_tab = ttk.Frame(tabs, padding=10)
        perf_tab = ttk.Frame(tabs, padding=10)
        tabs.add(restore_tab, text=self.t("restore_tab"))
        tabs.add(perf_tab, text=self.t("performance_tab"))
        restore_tab.columnconfigure(1, weight=1)
        perf_tab.columnconfigure(1, weight=1)

        ttk.Label(restore_tab, text=self.t("method")).grid(row=0, column=0, sticky="w", pady=4)
        self.method_combo = ttk.Combobox(
            restore_tab, state="readonly", values=[self.t("mixed"), self.t("telea"), self.t("ns")]
        )
        self.method_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.method_combo.current({"mixed": 0, "telea": 1, "ns": 2}.get(self.method_var.get(), 0))

        sliders = (
            ("radius", self.radius_var, 1, 25),
            ("margin", self.margin_var, 0, 100),
            ("feather", self.feather_var, 0, 31),
            ("smoothing", self.smoothing_var, 0, 31),
        )
        for row, (key, var, lo, hi) in enumerate(sliders, start=1):
            ttk.Label(restore_tab, text=self.t(key)).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Scale(restore_tab, from_=lo, to=hi, variable=var).grid(row=row, column=1, sticky="ew", padx=(10, 0))

        ttk.Checkbutton(restore_tab, text=self.t("denoise"), variable=self.denoise_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(restore_tab, text=self.t("sharpen"), variable=self.sharpen_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(restore_tab, text=self.t("color"), variable=self.color_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Label(restore_tab, text=self.t("quality")).grid(row=8, column=0, sticky="w", pady=4)
        self.quality_combo = ttk.Combobox(
            restore_tab, state="readonly", values=[self.t("fast"), self.t("balanced"), self.t("high")]
        )
        self.quality_combo.grid(row=8, column=1, sticky="ew", padx=(10, 0))
        self.quality_combo.current({"fast": 0, "balanced": 1, "high": 2}.get(self.quality_var.get(), 2))

        ttk.Label(perf_tab, text=self.t("codec")).grid(row=0, column=0, sticky="w", pady=4)
        self.codec_combo = ttk.Combobox(
            perf_tab, state="readonly", values=[self.t("mp4v"), self.t("h264"), self.t("xvid")]
        )
        self.codec_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.codec_combo.current({"mp4v": 0, "h264": 1, "xvid": 2}.get(self.codec_var.get(), 0))
        ttk.Label(perf_tab, text=self.t("workers")).grid(row=1, column=0, sticky="w", pady=4)
        worker_box = ttk.Spinbox(perf_tab, from_=1, to=8, textvariable=self.workers_var, width=8)
        worker_box.grid(row=1, column=1, sticky="w", padx=(10, 0))
        ttk.Checkbutton(perf_tab, text=self.t("hardware"), variable=self.hw_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(perf_tab, text=self.t("buffering"), variable=self.buffering_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(perf_tab, text=self.t("audio"), variable=self.audio_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(right, text=self.t("notice"), foreground="#ffcf66", wraplength=390).pack(fill="x", pady=(10, 0))

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(12, 0))
        ttk.Progressbar(bottom, variable=self.progress_var, maximum=100).pack(fill="x")
        actions = ttk.Frame(bottom)
        actions.pack(fill="x", pady=(6, 0))
        ttk.Label(actions, textvariable=self.status_var, foreground="#8ba3c7").pack(side="left")
        self.cancel_btn = ttk.Button(actions, text=self.t("cancel"), command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="right", padx=(6, 0))
        self.process_btn = ttk.Button(actions, text=self.t("process"), command=self._start)
        self.process_btn.pack(side="right")
        ttk.Button(actions, text="by Swir · GitHub", command=lambda: webbrowser.open("https://github.com/Swir")).pack(side="right", padx=(0, 12))
        self.status_var.set(self.t("status_ready"))
        self._rows()

    def _language(self, value: str) -> None:
        if value in STRINGS:
            self.language = value
            self.settings["language"] = value
            self._save()
            self._build()

    def _add(self) -> None:
        patterns = " ".join(f"*{e}" for e in sorted(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS))
        for raw in filedialog.askopenfilenames(filetypes=[("Media", patterns), ("All files", "*.*")]):
            path = Path(raw)
            try:
                media_kind(path)
            except ValueError:
                continue
            if path not in self.files:
                self.files.append(path)
        self._rows()

    def _remove(self) -> None:
        selected = set(self.tree.selection())
        self.files = [p for p in self.files if self.row_ids.get(p) not in selected]
        self._rows()

    def _clear(self) -> None:
        self.files.clear()
        self._rows()

    def _rows(self) -> None:
        if not hasattr(self, "tree"):
            return
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.row_ids.clear()
        for path in self.files:
            iid = self.tree.insert("", "end", text=str(path), values=(media_kind(path), self.t("pending")))
            self.row_ids[path] = iid

    def _browse(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.home()))
        if directory:
            self.output_var.set(directory)
            self._save()

    def _selected_corners(self) -> list[str]:
        return [key for key, variable in self.corner_vars.items() if variable.get()]

    def _areas_for_frame(self, frame) -> list[Area]:
        height, width = frame.shape[:2]
        return list(self.custom_areas) + corner_areas(width, height, self._selected_corners())

    def _select_areas(self) -> None:
        if not self.files:
            messagebox.showwarning(self.t("title"), self.t("no_files"))
            return
        try:
            frame = first_frame(self.files[0])
        except Exception as exc:
            messagebox.showerror(self.t("title"), str(exc))
            return
        height, width = frame.shape[:2]
        scale = min(1.0, 1100 / width, 700 / height)
        shown = cv2.resize(frame, (round(width * scale), round(height * scale))) if scale < 1 else frame
        self.status_var.set(self.t("select_areas_hint"))
        try:
            rois = cv2.selectROIs(self.t("title"), shown, showCrosshair=True, fromCenter=False)
        finally:
            cv2.destroyAllWindows()
        areas = [
            Area(round(x / scale), round(y / scale), round(rw / scale), round(rh / scale))
            for x, y, rw, rh in rois if rw > 2 and rh > 2
        ]
        if areas:
            self.custom_areas = areas
            self.area_label.configure(text=f"{self.t('areas')}: {len(areas)}")
            self._save()
            self.status_var.set(f"{self.t('area_saved')}: {len(areas)}")
        else:
            self.status_var.set(self.t("status_ready"))

    def _clear_areas(self) -> None:
        self.custom_areas = []
        self.area_label.configure(text=f"{self.t('areas')}: 0")
        self._save()
        self.status_var.set(self.t("areas_cleared"))

    @staticmethod
    def _areas_from_preset(raw: object) -> list[Area]:
        if not isinstance(raw, list):
            return []
        areas: list[Area] = []
        for item in raw:
            try:
                if isinstance(item, dict):
                    areas.append(Area.from_dict(item))
                elif isinstance(item, (list, tuple)) and len(item) >= 4:
                    areas.append(Area(int(item[0]), int(item[1]), int(item[2]), int(item[3])).normalized())
            except (TypeError, ValueError):
                continue
        return areas

    def _save_area_preset(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        options = self._options()
        payload = {
            "format": "watermark-remover-areas-v2",
            "areas": [area.to_dict() for area in self.custom_areas],
            "corners": {key: variable.get() for key, variable in self.corner_vars.items()},
            "settings": {
                "inpaint_method": options.method,
                "blur_strength": options.smoothing,
                "margin_size": options.margin,
            },
        }
        try:
            Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            self.status_var.set(f"{self.t('area_saved')}: {len(self.custom_areas)}")
        except OSError as exc:
            messagebox.showerror(self.t("title"), str(exc))

    def _load_area_preset(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(self.t("preset_invalid"))
            areas = self._areas_from_preset(data.get("areas", []))
            corners = data.get("corners", {})
            if isinstance(corners, dict):
                for key, variable in self.corner_vars.items():
                    if key in corners:
                        variable.set(bool(corners[key]))
            legacy_settings = data.get("settings", {})
            if isinstance(legacy_settings, dict):
                method = str(legacy_settings.get("inpaint_method", self.method_var.get()))
                if method in {"mixed", "telea", "ns"}:
                    self.method_var.set(method)
                    self.method_combo.current({"mixed": 0, "telea": 1, "ns": 2}[method])
                if "blur_strength" in legacy_settings:
                    self.smoothing_var.set(max(0, min(31, int(legacy_settings["blur_strength"]))))
                if "margin_size" in legacy_settings:
                    self.margin_var.set(max(0, min(100, int(legacy_settings["margin_size"]))))
            self.custom_areas = areas
            self.area_label.configure(text=f"{self.t('areas')}: {len(areas)}")
            self._save()
            self.status_var.set(f"{self.t('areas_loaded')}: {len(areas)}")
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            messagebox.showerror(self.t("title"), f"{self.t('preset_invalid')}\n{exc}")

    def _preview_result(self) -> None:
        if not self.files:
            messagebox.showwarning(self.t("title"), self.t("no_files"))
            return
        try:
            frame = first_frame(self.files[0])
            areas = self._areas_for_frame(frame)
            if not areas:
                messagebox.showwarning(self.t("title"), self.t("no_areas"))
                return
            result = process_frame(frame, areas, self._options())
        except Exception as exc:
            logging.exception("Preview failed")
            messagebox.showerror(self.t("title"), str(exc))
            return

        def photo(source) -> ImageTk.PhotoImage:
            rgb = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            image.thumbnail((520, 420), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)

        before = photo(frame)
        after = photo(result)
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.destroy()
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title(f"{self.t('preview_result')} · {self.files[0].name}")
        self.preview_window.geometry("1100x520")
        body = ttk.Frame(self.preview_window, padding=12)
        body.pack(fill="both", expand=True)
        left = ttk.LabelFrame(body, text="Before", padding=6)
        right = ttk.LabelFrame(body, text="After", padding=6)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Label(left, image=before).pack(expand=True)
        ttk.Label(right, image=after).pack(expand=True)
        self._preview_images = (before, after)

    def _options(self) -> ProcessingOptions:
        methods = ["mixed", "telea", "ns"]
        qualities = ["fast", "balanced", "high"]
        codecs = ["mp4v", "h264", "xvid"]
        options = ProcessingOptions(
            method=methods[max(0, self.method_combo.current())],
            radius=round(self.radius_var.get()),
            margin=round(self.margin_var.get()),
            feather=round(self.feather_var.get()),
            smoothing=round(self.smoothing_var.get()),
            denoise=self.denoise_var.get(),
            sharpen=self.sharpen_var.get(),
            color_correction=self.color_var.get(),
            preserve_audio=self.audio_var.get(),
            output_quality=qualities[max(0, self.quality_combo.current())],
            video_codec=codecs[max(0, self.codec_combo.current())],
            worker_count=int(self.workers_var.get()),
            hardware_acceleration=self.hw_var.get(),
            buffering=self.buffering_var.get(),
        )
        options.validate()
        return options

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.files:
            messagebox.showwarning(self.t("title"), self.t("no_files"))
            return
        if not self.output_var.get().strip():
            messagebox.showwarning(self.t("title"), self.t("no_output"))
            return
        output = Path(self.output_var.get()).expanduser()
        try:
            output.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(self.t("title"), str(exc))
            return

        opts = self._options()
        sources = list(self.files)
        custom = list(self.custom_areas)
        corners = self._selected_corners()
        if not custom and not corners:
            messagebox.showwarning(self.t("title"), self.t("no_areas"))
            return

        self.cancel_event.clear()
        self.process_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_var.set(0)
        self.status_var.set(self.t("status_processing"))
        self._save()

        def worker() -> None:
            total = max(1, len(sources))
            for pos, source in enumerate(sources):
                if self.cancel_event.is_set():
                    self.events.put(("cancel", None))
                    return
                try:
                    frame = first_frame(source)
                    height, width = frame.shape[:2]
                    areas = custom + corner_areas(width, height, corners)
                    kind = media_kind(source)
                    suffix = source.suffix.lower() if kind == "image" else opts.video_extension()
                    dest = output / f"{source.stem}_restored{suffix}"
                    self.events.put(("row", (source, self.t("status_processing"))))

                    def progress(ratio: float, detail: str) -> None:
                        self.events.put(("progress", (((pos + ratio) / total) * 100, f"{source.name} · {detail}")))

                    process_media(source, dest, areas, opts, self.cancel_event, progress)
                    self.events.put(("row", (source, self.t("done"))))
                except InterruptedError:
                    self.events.put(("row", (source, self.t("cancelled"))))
                    self.events.put(("cancel", None))
                    return
                except Exception as exc:
                    logging.exception("Failed %s", source)
                    self.events.put(("row", (source, self.t("failed"))))
                    self.events.put(("error", f"{source.name}: {exc}"))
            self.events.put(("done", None))

        self.worker = threading.Thread(target=worker, daemon=True, name="wmr-worker")
        self.worker.start()

    def _cancel(self) -> None:
        self.cancel_event.set()
        self.cancel_btn.configure(state="disabled")
        self.status_var.set(self.t("status_cancelled"))

    def _pump(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "progress":
                    value, detail = payload
                    self.progress_var.set(float(value))
                    self.status_var.set(str(detail))
                elif event == "row":
                    path, state = payload
                    iid = self.row_ids.get(path)
                    if iid:
                        self.tree.set(iid, "state", state)
                elif event == "error":
                    self.status_var.set(str(payload))
                elif event == "done":
                    self.progress_var.set(100)
                    self.status_var.set(self.t("status_done"))
                    self.process_btn.configure(state="normal")
                    self.cancel_btn.configure(state="disabled")
                elif event == "cancel":
                    self.status_var.set(self.t("status_cancelled"))
                    self.process_btn.configure(state="normal")
                    self.cancel_btn.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._pump)

    def _save(self) -> None:
        if hasattr(self, "method_combo"):
            self.settings.update(
                {
                    "language": self.language,
                    "output_dir": self.output_var.get(),
                    "last_options": asdict(self._options()),
                    "areas": [area.to_dict() for area in self.custom_areas],
                    "corners": {key: variable.get() for key, variable in self.corner_vars.items()},
                }
            )
        try:
            self.store.save(self.settings)
        except OSError:
            logging.exception("Settings save failed")

    def _close(self) -> None:
        self.cancel_event.set()
        self._save()
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.destroy()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    WatermarkRemoverApp(root)
    root.mainloop()
