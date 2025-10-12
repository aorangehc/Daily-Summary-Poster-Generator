import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List

from core.renderer import render_poster
from core.theme import THEMES, DEFAULT_THEME_ID
from modules.title import TitleModule
from modules.summary import SummaryModule
from modules.stats import StatsModule
from modules.quote import QuoteModule

try:
    from PIL import ImageTk
except Exception:  # pragma: no cover
    ImageTk = None


class AppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("每日总结海报生成器")
        self.root.geometry("1200x780")

        # State
        self.canvas_width = tk.IntVar(value=1240)
        self.canvas_height = tk.IntVar(value=1754)
        self.canvas_padding = tk.IntVar(value=64)
        self.scale = tk.DoubleVar(value=1.0)
        self.theme_id = tk.StringVar(value=DEFAULT_THEME_ID)

        self.modules: List[object] = [
            TitleModule(title="今日总结", subtitle="2025-06-01", align="left"),
            SummaryModule(items=["完成海报生成器设计", "实现模块化布局", "编写 README"], bullet="•"),
            StatsModule(title="今日数据", metrics=[{"label": "番茄", "value": "6"}, {"label": "步数", "value": "8123"}], columns=2),
            QuoteModule(text="不积跬步，无以至千里。", author="荀子"),
        ]
        self.selected_index = tk.IntVar(value=0)

        self._build_ui()
        self._refresh_preview()

    def run(self):
        self.root.mainloop()

    # UI construction
    def _build_ui(self):
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.grid(row=0, column=0, sticky="nsw")
        control_frame.columnconfigure(0, weight=1)

        # Canvas section
        ttk.Label(control_frame, text="画布与主题").grid(row=0, column=0, sticky="w", pady=(0, 6))
        canvas_box = ttk.Labelframe(control_frame, text="设置", padding=8)
        canvas_box.grid(row=1, column=0, sticky="new", pady=(0, 10))
        for i in range(2):
            canvas_box.columnconfigure(i, weight=1)

        ttk.Label(canvas_box, text="宽").grid(row=0, column=0, sticky="w")
        ttk.Entry(canvas_box, textvariable=self.canvas_width, width=10).grid(row=0, column=1, sticky="e")
        ttk.Label(canvas_box, text="高").grid(row=1, column=0, sticky="w")
        ttk.Entry(canvas_box, textvariable=self.canvas_height, width=10).grid(row=1, column=1, sticky="e")
        ttk.Label(canvas_box, text="边距").grid(row=2, column=0, sticky="w")
        ttk.Entry(canvas_box, textvariable=self.canvas_padding, width=10).grid(row=2, column=1, sticky="e")
        ttk.Label(canvas_box, text="主题").grid(row=3, column=0, sticky="w")
        theme_cb = ttk.Combobox(canvas_box, textvariable=self.theme_id, values=list(THEMES.keys()), state="readonly")
        theme_cb.grid(row=3, column=1, sticky="ew")
        ttk.Label(canvas_box, text="导出倍率").grid(row=4, column=0, sticky="w")
        ttk.Entry(canvas_box, textvariable=self.scale, width=10).grid(row=4, column=1, sticky="e")

        ttk.Button(canvas_box, text="应用设置", command=self._on_apply_settings).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        # Modules section
        ttk.Label(control_frame, text="模块").grid(row=2, column=0, sticky="w")
        mod_frame = ttk.Frame(control_frame)
        mod_frame.grid(row=3, column=0, sticky="new")
        mod_frame.columnconfigure(0, weight=1)
        mod_frame.rowconfigure(1, weight=1)

        self.module_list = tk.Listbox(mod_frame, height=12)
        self.module_list.grid(row=0, column=0, columnspan=3, sticky="new")
        self.module_list.bind("<<ListboxSelect>>", self._on_select_module)

        ttk.Button(mod_frame, text="上移", command=self._move_up).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(mod_frame, text="下移", command=self._move_down).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(mod_frame, text="删除", command=self._delete_module).grid(row=1, column=2, sticky="ew", pady=4)

        add_frame = ttk.Frame(mod_frame)
        add_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        ttk.Button(add_frame, text="新增标题", command=lambda: self._add_module("title")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(add_frame, text="新增摘要", command=lambda: self._add_module("summary")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(add_frame, text="新增统计", command=lambda: self._add_module("stats")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(add_frame, text="新增金句", command=lambda: self._add_module("quote")).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Editor section
        self.editor_box = ttk.Labelframe(control_frame, text="模块编辑", padding=8)
        self.editor_box.grid(row=4, column=0, sticky="new", pady=(10, 0))
        self._build_editors()

        # Right preview
        right = ttk.Frame(self.root, padding=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(right)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        bottom = ttk.Frame(right)
        bottom.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(bottom, text="导出 PNG", command=self._export_png).pack(side=tk.LEFT)

        self._refresh_module_list()

    def _build_editors(self):
        for child in self.editor_box.winfo_children():
            child.destroy()

        idx = self.selected_index.get()
        if not (0 <= idx < len(self.modules)):
            ttk.Label(self.editor_box, text="请选择一个模块").pack(anchor="w")
            return
        mod = self.modules[idx]

        if isinstance(mod, TitleModule):
            self._build_title_editor(mod)
        elif isinstance(mod, SummaryModule):
            self._build_summary_editor(mod)
        elif isinstance(mod, StatsModule):
            self._build_stats_editor(mod)
        elif isinstance(mod, QuoteModule):
            self._build_quote_editor(mod)

    def _build_title_editor(self, mod: TitleModule):
        title_var = tk.StringVar(value=mod.title)
        sub_var = tk.StringVar(value=mod.subtitle)
        align_var = tk.StringVar(value=mod.align)

        ttk.Label(self.editor_box, text="主标题").pack(anchor="w")
        ttk.Entry(self.editor_box, textvariable=title_var).pack(fill=tk.X)

        ttk.Label(self.editor_box, text="副标题/日期").pack(anchor="w", pady=(6, 0))
        ttk.Entry(self.editor_box, textvariable=sub_var).pack(fill=tk.X)

        ttk.Label(self.editor_box, text="对齐").pack(anchor="w", pady=(6, 0))
        align_frame = ttk.Frame(self.editor_box)
        align_frame.pack(anchor="w")
        ttk.Radiobutton(align_frame, text="左对齐", value="left", variable=align_var).pack(side=tk.LEFT)
        ttk.Radiobutton(align_frame, text="居中", value="center", variable=align_var).pack(side=tk.LEFT)

        def apply():
            mod.title = title_var.get()
            mod.subtitle = sub_var.get()
            mod.align = align_var.get()
            self._refresh_preview()

        ttk.Button(self.editor_box, text="应用", command=apply).pack(fill=tk.X, pady=(8, 0))

    def _build_summary_editor(self, mod: SummaryModule):
        items_text = tk.Text(self.editor_box, height=6)
        items_text.insert("1.0", "\n".join(mod.items))
        ttk.Label(self.editor_box, text="要点（每行一个）").pack(anchor="w")
        items_text.pack(fill=tk.BOTH)

        bullet_var = tk.StringVar(value=mod.bullet)
        ttk.Label(self.editor_box, text="前缀符号").pack(anchor="w", pady=(6, 0))
        ttk.Combobox(self.editor_box, textvariable=bullet_var, values=["•", "—", "✓", "·"], state="readonly").pack(fill=tk.X)

        def apply():
            text = items_text.get("1.0", tk.END).strip()
            mod.items = [line.strip() for line in text.splitlines() if line.strip()]
            mod.bullet = bullet_var.get()
            self._refresh_preview()

        ttk.Button(self.editor_box, text="应用", command=apply).pack(fill=tk.X, pady=(8, 0))

    def _build_stats_editor(self, mod: StatsModule):
        ttk.Label(self.editor_box, text="统计项（每行 label:value）").pack(anchor="w")
        items_text = tk.Text(self.editor_box, height=6)
        items_text.insert("1.0", "\n".join(f"{m['label']}:{m['value']}" for m in mod.metrics))
        items_text.pack(fill=tk.BOTH)

        cols_var = tk.IntVar(value=mod.columns)
        ttk.Label(self.editor_box, text="列数").pack(anchor="w", pady=(6, 0))
        ttk.Spinbox(self.editor_box, from_=1, to=4, textvariable=cols_var).pack(fill=tk.X)

        def apply():
            text = items_text.get("1.0", tk.END).strip()
            metrics = []
            for line in text.splitlines():
                if ":" in line:
                    label, value = line.split(":", 1)
                    metrics.append({"label": label.strip(), "value": value.strip()})
            mod.metrics = metrics
            mod.columns = max(1, min(4, cols_var.get()))
            self._refresh_preview()

        ttk.Button(self.editor_box, text="应用", command=apply).pack(fill=tk.X, pady=(8, 0))

    def _build_quote_editor(self, mod: QuoteModule):
        text_var = tk.StringVar(value=mod.text)
        author_var = tk.StringVar(value=mod.author)
        ttk.Label(self.editor_box, text="内容").pack(anchor="w")
        ttk.Entry(self.editor_box, textvariable=text_var).pack(fill=tk.X)
        ttk.Label(self.editor_box, text="作者/来源").pack(anchor="w", pady=(6, 0))
        ttk.Entry(self.editor_box, textvariable=author_var).pack(fill=tk.X)

        def apply():
            mod.text = text_var.get()
            mod.author = author_var.get()
            self._refresh_preview()

        ttk.Button(self.editor_box, text="应用", command=apply).pack(fill=tk.X, pady=(8, 0))

    # Module ops
    def _add_module(self, mtype: str):
        if mtype == "title":
            self.modules.append(TitleModule(title="标题", subtitle="日期", align="left"))
        elif mtype == "summary":
            self.modules.append(SummaryModule(items=["要点 A", "要点 B"], bullet="•"))
        elif mtype == "stats":
            self.modules.append(StatsModule(title="数据", metrics=[{"label": "项", "value": "值"}], columns=2))
        elif mtype == "quote":
            self.modules.append(QuoteModule(text="金句", author="——"))
        self.selected_index.set(len(self.modules) - 1)
        self._refresh_module_list()
        self._build_editors()
        self._refresh_preview()

    def _delete_module(self):
        idx = self.selected_index.get()
        if 0 <= idx < len(self.modules):
            self.modules.pop(idx)
            self.selected_index.set(max(0, idx - 1))
            self._refresh_module_list()
            self._build_editors()
            self._refresh_preview()

    def _move_up(self):
        idx = self.selected_index.get()
        if idx > 0:
            self.modules[idx - 1], self.modules[idx] = self.modules[idx], self.modules[idx - 1]
            self.selected_index.set(idx - 1)
            self._refresh_module_list()

    def _move_down(self):
        idx = self.selected_index.get()
        if idx < len(self.modules) - 1:
            self.modules[idx + 1], self.modules[idx] = self.modules[idx], self.modules[idx + 1]
            self.selected_index.set(idx + 1)
            self._refresh_module_list()

    def _on_select_module(self, _evt=None):
        try:
            idxs = self.module_list.curselection()
            if not idxs:
                return
            self.selected_index.set(int(idxs[0]))
            self._build_editors()
        finally:
            self._refresh_preview()

    def _on_apply_settings(self):
        self._refresh_preview()

    def _refresh_module_list(self):
        self.module_list.delete(0, tk.END)
        for mod in self.modules:
            name = getattr(mod, "name", mod.__class__.__name__)
            self.module_list.insert(tk.END, name)
        if 0 <= self.selected_index.get() < len(self.modules):
            self.module_list.selection_clear(0, tk.END)
            self.module_list.selection_set(self.selected_index.get())
            self.module_list.activate(self.selected_index.get())

    def _refresh_preview(self):
        try:
            img = render_poster(
                modules=self.modules,
                theme_id=self.theme_id.get(),
                width=self.canvas_width.get(),
                height=self.canvas_height.get(),
                padding=self.canvas_padding.get(),
                scale=1.0,
            )
            # Fit to preview width ~ 700px
            target_w = 700
            ratio = target_w / img.width
            preview_img = img.resize((int(img.width * ratio), int(img.height * ratio)))
            if ImageTk is None:
                return
            self._preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_label.configure(image=self._preview_photo)
        except Exception as e:
            # soft-fail to avoid UI crash
            self.preview_label.configure(text=f"预览出错: {e}")

    def _export_png(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG 图片", "*.png")], title="导出 PNG"
        )
        if not path:
            return
        try:
            img = render_poster(
                modules=self.modules,
                theme_id=self.theme_id.get(),
                width=self.canvas_width.get(),
                height=self.canvas_height.get(),
                padding=self.canvas_padding.get(),
                scale=max(1.0, float(self.scale.get() or 1.0)),
            )
            img.save(path)
            messagebox.showinfo("导出成功", f"已导出到:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

