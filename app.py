"""Load a chart image, select an area, and rotate that area by 180 degrees."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk


def selected_image_box(
    start: tuple[float, float],
    end: tuple[float, float],
    display_rect: tuple[float, float, float, float],
    image_size: tuple[int, int],
) -> tuple[int, int, int, int] | None:
    """Convert a drag on the displayed image into a Pillow crop box."""
    left, top, right, bottom = display_rect
    if right <= left or bottom <= top:
        return None
    x1, x2 = sorted((max(left, min(right, start[0])), max(left, min(right, end[0]))))
    y1, y2 = sorted((max(top, min(bottom, start[1])), max(top, min(bottom, end[1]))))
    if x2 - x1 < 3 or y2 - y1 < 3:
        return None
    width, height = image_size
    box = (
        round((x1 - left) * width / (right - left)),
        round((y1 - top) * height / (bottom - top)),
        round((x2 - left) * width / (right - left)),
        round((y2 - top) * height / (bottom - top)),
    )
    return box if box[2] > box[0] and box[3] > box[1] else None


def reflect_region(
    source: Image.Image, box: tuple[int, int, int, int] | None = None
) -> Image.Image:
    """Match cv2.flip(image, -1): reverse both axes without scaling pixels."""
    if box is not None:
        left, top, right, bottom = box
        if not (0 <= left < right <= source.width and 0 <= top < bottom <= source.height):
            raise ValueError("選取範圍超出圖片")
        source = source.crop(box)
    return source.transpose(Image.Transpose.ROTATE_180)


class ReflectionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("圖表雙重反射｜圖片觀察工具")
        self.root.minsize(980, 580)
        self.source: Image.Image | None = None
        self.result: Image.Image | None = None
        self.selection: tuple[int, int, int, int] | None = None
        self.display_rect: tuple[float, float, float, float] | None = None
        self.drag_start: tuple[float, float] | None = None
        self.source_photo: ImageTk.PhotoImage | None = None
        self.result_photo: ImageTk.PhotoImage | None = None

        container = ttk.Frame(root, padding=12)
        container.pack(fill="both", expand=True)

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="① 選擇圖片", command=self.open_image).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="清除選取（使用全圖）", command=self.clear_selection).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(actions, text="② 產生反射圖", command=self.generate).pack(
            side="left", padx=(0, 8)
        )
        self.save_button = ttk.Button(actions, text="③ 另存反射圖", command=self.save_image)
        self.save_button.pack(side="left")
        self.save_button.state(["disabled"])

        ttk.Label(
            container,
            text="在左圖拖曳欲觀察的圖表區域；不選取就會旋轉整張圖片。右圖為旋轉 180° 的結果。",
        ).pack(anchor="w", pady=(0, 8))

        panels = ttk.Frame(container)
        panels.pack(fill="both", expand=True)
        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(1, weight=1)
        panels.rowconfigure(1, weight=1)
        ttk.Label(panels, text="原圖（拖曳選取）").grid(row=0, column=0, sticky="w")
        ttk.Label(panels, text="反射預覽").grid(row=0, column=1, sticky="w")
        self.source_canvas = tk.Canvas(panels, bg="#14202a", highlightthickness=0)
        self.result_canvas = tk.Canvas(panels, bg="#14202a", highlightthickness=0)
        self.source_canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.result_canvas.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

        self.status = tk.StringVar(value="請先選擇一張 PNG、JPG、WEBP 或 BMP 圖片。")
        ttk.Label(container, textvariable=self.status).pack(anchor="w", pady=(8, 0))
        ttk.Label(container, text="僅供圖形觀察；旋轉影像不能推論未來走勢。", foreground="#555").pack(
            anchor="w", pady=(2, 0)
        )

        self.source_canvas.bind("<ButtonPress-1>", self._on_press)
        self.source_canvas.bind("<B1-Motion>", self._on_drag)
        self.source_canvas.bind("<ButtonRelease-1>", self._on_release)
        self.source_canvas.bind("<Configure>", lambda _event: self._render_source())
        self.result_canvas.bind("<Configure>", lambda _event: self._render_result())
        root.bind("<Control-o>", lambda _event: self.open_image())
        root.bind("<Control-s>", lambda _event: self.save_image())

    def open_image(self) -> None:
        filename = filedialog.askopenfilename(
            title="選擇圖表截圖",
            filetypes=[("圖片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有檔案", "*.*")],
        )
        if not filename:
            return
        try:
            with Image.open(filename) as image:
                # Respect phone screenshot orientation and release the file handle.
                source = ImageOps.exif_transpose(image).convert("RGB")
                source.load()
        except (OSError, ValueError) as exc:
            messagebox.showerror("無法開啟圖片", str(exc))
            return
        self.source = source
        self.selection = None
        self.result = None
        self.save_button.state(["disabled"])
        self._render_source()
        self._render_result()
        self.status.set(f"已載入 {Path(filename).name}（{source.width} × {source.height}）；可拖曳範圍。")

    def clear_selection(self) -> None:
        self.selection = None
        self.result = None
        self.save_button.state(["disabled"])
        self._render_source()
        self._render_result()
        if self.source is not None:
            self.status.set("已清除範圍；按『產生反射圖』會使用整張圖片。")

    def generate(self) -> None:
        if self.source is None:
            messagebox.showinfo("尚未選擇圖片", "請先選擇一張圖表截圖。")
            return
        self.result = reflect_region(self.source, self.selection)
        self._render_result()
        self.save_button.state(["!disabled"])
        self.status.set(f"已產生 {self.result.width} × {self.result.height} 的反射圖，可另存 PNG 或 JPG。")

    def save_image(self) -> None:
        if self.result is None:
            return
        filename = filedialog.asksaveasfilename(
            title="另存反射圖",
            defaultextension=".png",
            initialfile="reflection.png",
            filetypes=[("PNG 圖片", "*.png"), ("JPEG 圖片", "*.jpg")],
        )
        if not filename:
            return
        try:
            self.result.save(filename)
        except (OSError, ValueError) as exc:
            messagebox.showerror("儲存失敗", str(exc))
            return
        self.status.set(f"已儲存：{filename}")

    @staticmethod
    def _fit(image: Image.Image, canvas: tk.Canvas) -> tuple[Image.Image, float, float]:
        width, height = max(1, canvas.winfo_width() - 20), max(1, canvas.winfo_height() - 20)
        preview = image.copy()
        preview.thumbnail((width, height), Image.Resampling.LANCZOS)
        return preview, (canvas.winfo_width() - preview.width) / 2, (
            canvas.winfo_height() - preview.height
        ) / 2

    def _render_source(self) -> None:
        self.source_canvas.delete("all")
        self.display_rect = None
        if self.source is None:
            return
        preview, x, y = self._fit(self.source, self.source_canvas)
        self.source_photo = ImageTk.PhotoImage(preview)
        self.source_canvas.create_image(x, y, anchor="nw", image=self.source_photo)
        self.display_rect = (x, y, x + preview.width, y + preview.height)
        if self.selection:
            a, b, c, d = self.selection
            self.source_canvas.create_rectangle(
                x + a * preview.width / self.source.width,
                y + b * preview.height / self.source.height,
                x + c * preview.width / self.source.width,
                y + d * preview.height / self.source.height,
                outline="#00ccaa", width=2, tags="selection",
            )

    def _render_result(self) -> None:
        self.result_canvas.delete("all")
        if self.result is None:
            return
        preview, x, y = self._fit(self.result, self.result_canvas)
        self.result_photo = ImageTk.PhotoImage(preview)
        self.result_canvas.create_image(x, y, anchor="nw", image=self.result_photo)

    def _on_press(self, event: tk.Event) -> None:
        if self.source is None or self.display_rect is None:
            return
        left, top, right, bottom = self.display_rect
        if left <= event.x <= right and top <= event.y <= bottom:
            self.drag_start = (event.x, event.y)

    def _on_drag(self, event: tk.Event) -> None:
        if self.drag_start is None or self.display_rect is None:
            return
        left, top, right, bottom = self.display_rect
        self.source_canvas.delete("selection")
        self.source_canvas.create_rectangle(
            *self.drag_start,
            max(left, min(right, event.x)), max(top, min(bottom, event.y)),
            outline="#00ccaa", width=2, tags="selection",
        )

    def _on_release(self, event: tk.Event) -> None:
        if self.drag_start is None or self.display_rect is None or self.source is None:
            return
        box = selected_image_box(
            self.drag_start, (event.x, event.y), self.display_rect, self.source.size
        )
        self.drag_start = None
        if box is None:
            self._render_source()
            self.status.set("選取範圍太小；請重新拖曳，或使用整張圖片。")
            return
        self.selection = box
        self.result = None
        self.save_button.state(["disabled"])
        self._render_source()
        self._render_result()
        self.status.set(f"已選取 {box[2] - box[0]} × {box[3] - box[1]}；請按『產生反射圖』。")


def main() -> int:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"無法啟動圖形介面：{exc}", file=sys.stderr)
        return 1
    ReflectionApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
