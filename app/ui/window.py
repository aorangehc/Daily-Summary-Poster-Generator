import os
import json
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import List

from app.core.renderer import render_poster
from app.core.theme import THEMES, DEFAULT_THEME_ID
from app.core import storage
from app.modules.title import TitleModule
from app.modules.summary import SummaryModule
from app.modules.stats import StatsModule
from app.modules.quote import QuoteModule
from app.modules.rich import RichModule
from app.modules.image import ImageModule

try:
    from PIL import ImageTk
except Exception:
    ImageTk = None


class AppWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("每日总结海报生成器")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # State
        self.canvas_width = tk.IntVar(value=1240)
        self.canvas_height = tk.IntVar(value=1754)
        self.canvas_padding = tk.IntVar(value=64)
        self.canvas_dpi = tk.IntVar(value=150)
        self.scale = tk.DoubleVar(value=1.0)
        self.theme_id = tk.StringVar(value=DEFAULT_THEME_ID)
        self.bg_color = tk.StringVar(value="")
        self.bg_gradient: dict | None = None

        self.modules: List[object] = [
            TitleModule(title="今日总结", subtitle="2025-06-01", align="left"),
            SummaryModule(items=["完成海报生成器设计", "实现模块化布局", "编写 README"], bullet="•"),
            StatsModule(title="今日数据", metrics=[{"label": "番茄", "value": "6"}, {"label": "步数", "value": "8123"}], columns=2),
            QuoteModule(text="不积跬步，无以至千里。", author="荀子"),
        ]
        self.selected_index = tk.IntVar(value=0)
        self.current_path: str | None = None

        self._build_ui()
        self._refresh_preview()

    def run(self):
        self.root.mainloop()

    # UI construction
    def _build_ui(self):
        # Menubar
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建", command=self._new_config)
        file_menu.add_command(label="打开...", command=self._open_config)
        file_menu.add_command(label="保存", command=self._save_config)
        file_menu.add_command(label="另存为...", command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="从模板新建...", command=self._new_from_template)
        menubar.add_cascade(label="文件", menu=file_menu)

        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="主题调色板...", command=self._open_theme_editor)
        menubar.add_cascade(label="主题", menu=theme_menu)
        self.root.config(menu=menubar)

        self.root.columnconfigure(0, weight=0, minsize=450)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left scrollable panel
        self.left_panel = _ScrollableFrame(self.root, padding=10)
        # Ensure left panel has visible width
        self.left_panel.configure(width=450)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        control_frame = self.left_panel.body
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
        self.theme_cb = ttk.Combobox(canvas_box, textvariable=self.theme_id, values=list(THEMES.keys()), state="readonly")
        self.theme_cb.grid(row=3, column=1, sticky="ew")
        ttk.Label(canvas_box, text="导出倍率").grid(row=4, column=0, sticky="w")
        ttk.Entry(canvas_box, textvariable=self.scale, width=10).grid(row=4, column=1, sticky="e")
        # Background override controls
        ttk.Label(canvas_box, text="背景颜色").grid(row=5, column=0, sticky="w")
        bg_row = ttk.Frame(canvas_box)
        bg_row.grid(row=5, column=1, sticky="ew")
        ttk.Entry(bg_row, textvariable=self.bg_color).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bg_row, text="选择", command=self._pick_bg_color).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bg_row, text="清除", command=lambda: self.bg_color.set("")).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(canvas_box, text="背景渐变...", command=self._open_bg_editor).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        ttk.Button(canvas_box, text="应用设置", command=self._on_apply_settings).grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0))

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

        add2 = ttk.Frame(mod_frame)
        add2.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Button(add2, text="新增自定义模块", command=lambda: self._add_module("rich")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(add2, text="新增图片/贴纸", command=lambda: self._add_module("image")).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Editor section
        self.editor_box = ttk.Labelframe(control_frame, text="模块编辑", padding=8)
        self.editor_box.grid(row=4, column=0, sticky="new", pady=(10, 0))
        self._build_editors()

        # Right preview
        self.right = ttk.Frame(self.root, padding=10)
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(self.right)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        bottom = ttk.Frame(self.right)
        bottom.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(bottom, text="导出 PNG", command=self._export_png).pack(side=tk.LEFT)
        ttk.Button(bottom, text="保存配置", command=self._save_config).pack(side=tk.LEFT, padx=(8, 0))

        # refresh initial themes list
        self._refresh_theme_values()
        # refresh initial module list and editors
        self._refresh_module_list()
        self._build_editors()
        # re-render preview when window resizes
        self.root.bind("<Configure>", lambda e: self._refresh_preview())

    def _build_editors(self):
        for child in self.editor_box.winfo_children():
            child.destroy()

        idx = self.selected_index.get()
        if not (0 <= idx < len(self.modules)):
            ttk.Label(self.editor_box, text="请选择一个模块").pack(anchor="w")
            return
        mod = self.modules[idx]

        ttk.Button(self.editor_box, text="高级样式...", command=lambda m=mod: self._open_style_editor(m)).pack(fill=tk.X, pady=(0, 8))

        if isinstance(mod, TitleModule):
            self._build_title_editor(mod)
        elif isinstance(mod, SummaryModule):
            self._build_summary_editor(mod)
        elif isinstance(mod, StatsModule):
            self._build_stats_editor(mod)
        elif isinstance(mod, QuoteModule):
            self._build_quote_editor(mod)
        elif isinstance(mod, RichModule):
            self._build_rich_editor(mod)
        elif isinstance(mod, ImageModule):
            self._build_image_editor(mod)

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

    def _build_rich_editor(self, mod: RichModule):
        title_var = tk.StringVar(value=mod.title or "")
        body_text = tk.Text(self.editor_box, height=6)
        body_text.insert("1.0", mod.body or "")
        items_text = tk.Text(self.editor_box, height=4)
        items_text.insert("1.0", "\n".join(mod.items))
        align_var = tk.StringVar(value=mod.align)

        ttk.Label(self.editor_box, text="标题").pack(anchor="w")
        ttk.Entry(self.editor_box, textvariable=title_var).pack(fill=tk.X)
        ttk.Label(self.editor_box, text="正文").pack(anchor="w", pady=(6, 0))
        body_text.pack(fill=tk.BOTH)
        ttk.Label(self.editor_box, text="列表（每行一项）").pack(anchor="w", pady=(6, 0))
        items_text.pack(fill=tk.BOTH)
        ttk.Label(self.editor_box, text="对齐").pack(anchor="w", pady=(6, 0))
        af = ttk.Frame(self.editor_box)
        af.pack(anchor="w")
        ttk.Radiobutton(af, text="左对齐", variable=align_var, value="left").pack(side=tk.LEFT)
        ttk.Radiobutton(af, text="居中", variable=align_var, value="center").pack(side=tk.LEFT)

        def apply():
            mod.title = (title_var.get() or None)
            mod.body = body_text.get("1.0", tk.END).strip() or None
            mod.items = [ln.strip() for ln in items_text.get("1.0", tk.END).strip().splitlines() if ln.strip()]
            mod.align = align_var.get()
            self._refresh_preview()

        ttk.Button(self.editor_box, text="应用", command=apply).pack(fill=tk.X, pady=(8, 0))

    def _build_image_editor(self, mod: ImageModule):
        path_var = tk.StringVar(value=mod.path)
        fit_var = tk.StringVar(value=mod.fit)
        h_var = tk.IntVar(value=mod.height)
        row = ttk.Frame(self.editor_box)
        row.pack(fill=tk.X)
        ttk.Entry(row, textvariable=path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="选择图片", command=lambda: self._choose_image(path_var)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Label(self.editor_box, text="填充方式").pack(anchor="w", pady=(6, 0))
        ttk.Combobox(self.editor_box, textvariable=fit_var, values=["cover", "contain"], state="readonly").pack(fill=tk.X)
        ttk.Label(self.editor_box, text="高度(px)").pack(anchor="w", pady=(6, 0))
        ttk.Spinbox(self.editor_box, from_=60, to=1200, textvariable=h_var).pack(fill=tk.X)

        def apply():
            mod.path = path_var.get()
            mod.fit = fit_var.get()
            mod.height = int(h_var.get())
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
        elif mtype == "rich":
            self.modules.append(RichModule(title="模块标题", body="这里是正文，可以包含 emoji 🙂 和换行。", items=["要点一", "要点二"]))
        elif mtype == "image":
            self.modules.append(ImageModule(path="", fit="cover", height=200))
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
                bg_color_override=(self.bg_color.get() or None),
                bg_gradient_override=self.bg_gradient,
            )
            # Fit to preview container width, but not enlarge
            if ImageTk is None:
                return
            # compute available width in right panel
            try:
                avail = max(300, self.right.winfo_width() - 20)
            except Exception:
                avail = 700
            target_w = avail
            ratio = min(target_w / img.width, 1.0)
            preview_img = img if ratio >= 1.0 else img.resize((int(img.width * ratio), int(img.height * ratio)))
            self._preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_label.configure(image=self._preview_photo)
        except Exception as e:
            self.preview_label.configure(text=f"预览出错: {e}")

    def _export_png(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG 图片", "*.png")], title="导出 PNG"
        )
        if not path:
            return
        try:
            try:
                scale_val = float(self.scale.get())
            except Exception:
                scale_val = 1.0
            scale_val = max(1.0, scale_val)
            img = render_poster(
                modules=self.modules,
                theme_id=self.theme_id.get(),
                width=self.canvas_width.get(),
                height=self.canvas_height.get(),
                padding=self.canvas_padding.get(),
                scale=scale_val,
                bg_color_override=(self.bg_color.get() or None),
                bg_gradient_override=self.bg_gradient,
            )
            img.save(path)
            messagebox.showinfo("导出成功", f"已导出到:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    # File ops
    def _new_config(self):
        self.modules = [TitleModule(title="今日总结", subtitle="2025-06-01", align="left")]
        self.theme_id.set(DEFAULT_THEME_ID)
        self.canvas_width.set(1240)
        self.canvas_height.set(1754)
        self.canvas_padding.set(64)
        self.canvas_dpi.set(150)
        self.scale.set(1.0)
        self.current_path = None
        self._refresh_module_list()
        self._build_editors()
        self._refresh_theme_values()
        self._refresh_preview()

    def _open_config(self):
        path = filedialog.askopenfilename(filetypes=[("Poster JSON", "*.poster.json"), ("JSON", "*.json")])
        if not path:
            return
        try:
            data = storage.load_config(path)
            self._load_from_data(data)
            self.current_path = path
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    def _save_config(self):
        if not self.current_path:
            return self._save_as()
        try:
            data = self._to_data()
            storage.save_config(self.current_path, data)
            messagebox.showinfo("保存成功", self.current_path)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".poster.json", filetypes=[("Poster JSON", "*.poster.json"), ("JSON", "*.json")])
        if not path:
            return
        self.current_path = path
        self._save_config()

    def _new_from_template(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'examples', 'templates')
        base = os.path.abspath(base)
        if not os.path.isdir(base):
            messagebox.showinfo("模板", "没有找到模板目录：examples/templates")
            return
        files = [f for f in os.listdir(base) if f.endswith('.poster.json')]
        if not files:
            messagebox.showinfo("模板", "模板目录为空")
            return
        top = tk.Toplevel(self.root)
        top.title("选择模板")
        lb = tk.Listbox(top, width=50, height=8)
        lb.pack(fill=tk.BOTH, expand=True)
        for f in files:
            lb.insert(tk.END, f)

        def use_sel():
            sel = lb.curselection()
            if not sel:
                return
            fp = os.path.join(base, files[sel[0]])
            try:
                data = storage.load_config(fp)
                self._load_from_data(data)
                self.current_path = None
            except Exception as e:
                messagebox.showerror("加载模板失败", str(e))
            finally:
                top.destroy()

        ttk.Button(top, text="使用此模板", command=use_sel).pack(fill=tk.X)

    def _refresh_theme_values(self):
        vals = list(THEMES.keys())
        self.theme_cb.configure(values=vals)
        if self.theme_id.get() not in vals:
            self.theme_id.set(DEFAULT_THEME_ID)

    def _load_from_data(self, data: dict):
        canvas = data.get('canvas', {})
        self.canvas_width.set(int(canvas.get('width', 1240)))
        self.canvas_height.set(int(canvas.get('height', 1754)))
        self.canvas_padding.set(int(canvas.get('padding', 64)))
        self.canvas_dpi.set(int(canvas.get('dpi', 150)))
        self.bg_color.set(str(canvas.get('bg_color', '')))
        self.bg_gradient = canvas.get('bg_gradient') or None

        theme = data.get('theme', DEFAULT_THEME_ID)
        theme_data = data.get('theme_data')
        if theme_data:
            # stable unique id for loaded theme
            digest = hashlib.md5(json.dumps(theme_data, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:8]
            tid = f"loaded-{digest}"
            THEMES[tid] = theme_data
            self.theme_id.set(tid)
        else:
            self.theme_id.set(theme)
        self._refresh_theme_values()

        self.modules = []
        for m in data.get('modules', []):
            mtype = m.get('type')
            style = m.get('style', {})
            if mtype == 'title':
                self.modules.append(TitleModule(title=m.get('title', ''), subtitle=m.get('subtitle', ''), align=m.get('align', 'left'), style=style))
            elif mtype == 'summary':
                self.modules.append(SummaryModule(title=m.get('title', ''), items=m.get('items', []), bullet=m.get('bullet', '•'), style=style))
            elif mtype == 'stats':
                self.modules.append(StatsModule(title=m.get('title', ''), metrics=m.get('metrics', []), columns=int(m.get('columns', 2)), style=style))
            elif mtype == 'quote':
                self.modules.append(QuoteModule(text=m.get('text', ''), author=m.get('author', ''), style=style))
            elif mtype == 'rich':
                self.modules.append(RichModule(title=m.get('title'), body=m.get('body'), items=m.get('items', []), image_path=m.get('image_path'), align=m.get('align', 'left'), style=style))
            elif mtype == 'image':
                self.modules.append(ImageModule(path=m.get('path', ''), fit=m.get('fit', 'cover'), height=int(m.get('height', 200)), style=style))
        self.selected_index.set(0 if self.modules else -1)
        self._refresh_module_list()
        self._build_editors()
        self._refresh_preview()

    def _to_data(self) -> dict:
        data = {
            'canvas': {
                'width': self.canvas_width.get(),
                'height': self.canvas_height.get(),
                'dpi': self.canvas_dpi.get(),
                'padding': self.canvas_padding.get(),
                'bg_color': (self.bg_color.get() or None),
                'bg_gradient': self.bg_gradient,
            },
            'theme': self.theme_id.get(),
            'modules': []
        }
        tid = self.theme_id.get()
        if tid in ('custom',) or tid.startswith('loaded-'):
            data['theme_data'] = THEMES.get(tid)
        for m in self.modules:
            if isinstance(m, TitleModule):
                data['modules'].append({'type': 'title', 'title': m.title, 'subtitle': m.subtitle, 'align': m.align, 'style': getattr(m, 'style', {})})
            elif isinstance(m, SummaryModule):
                data['modules'].append({'type': 'summary', 'title': m.title, 'items': m.items, 'bullet': m.bullet, 'style': getattr(m, 'style', {})})
            elif isinstance(m, StatsModule):
                data['modules'].append({'type': 'stats', 'title': m.title, 'metrics': m.metrics, 'columns': m.columns, 'style': getattr(m, 'style', {})})
            elif isinstance(m, QuoteModule):
                data['modules'].append({'type': 'quote', 'text': m.text, 'author': m.author, 'style': getattr(m, 'style', {})})
            elif isinstance(m, RichModule):
                data['modules'].append({'type': 'rich', 'title': m.title, 'body': m.body, 'items': m.items, 'image_path': getattr(m, 'image_path', None), 'align': m.align, 'style': getattr(m, 'style', {})})
            elif isinstance(m, ImageModule):
                data['modules'].append({'type': 'image', 'path': m.path, 'fit': m.fit, 'height': m.height, 'style': getattr(m, 'style', {})})
        return data

    # Style editor
    def _open_style_editor(self, mod):
        top = tk.Toplevel(self.root)
        top.title(f"样式：{getattr(mod, 'name', mod.__class__.__name__)}")
        s = dict(getattr(mod, 'style', {}))

        def pick_color(label, key):
            c = colorchooser.askcolor(title=label)
            if c and c[1]:
                s[key] = c[1]
                refresh()

        def toggle_gradient():
            if 'bg_gradient' in s and s['bg_gradient']:
                s['bg_gradient'] = None
            else:
                s['bg_gradient'] = {'start': '#FFDEE9', 'end': '#B5FFFC', 'angle': 90}
            refresh()

        def pick_grad(which: str):
            if not s.get('bg_gradient'):
                messagebox.showinfo('渐变', '请先开启渐变底色')
                return
            c = colorchooser.askcolor(title=f"选择渐变{which}色")
            if c and c[1]:
                s['bg_gradient'][which] = c[1]
                refresh()

        ttk.Button(top, text="文本颜色", command=lambda: pick_color('文本颜色', 'text_color')).pack(fill=tk.X)
        ttk.Button(top, text="强调色", command=lambda: pick_color('强调色', 'accent_color')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="卡片底色", command=lambda: pick_color('卡片底色', 'bg_color')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="切换渐变底色", command=toggle_gradient).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="渐变起始色", command=lambda: pick_grad('start')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="渐变结束色", command=lambda: pick_grad('end')).pack(fill=tk.X, pady=(4, 0))

        # radius & padding
        rp = ttk.Frame(top)
        rp.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(rp, text="圆角").pack(side=tk.LEFT)
        radius_var = tk.IntVar(value=int(s.get('radius', 20)))
        ttk.Spinbox(rp, from_=0, to=64, textvariable=radius_var, width=6).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(rp, text="内边距").pack(side=tk.LEFT)
        padding_var = tk.IntVar(value=int(s.get('padding', 24)))
        ttk.Spinbox(rp, from_=8, to=96, textvariable=padding_var, width=6).pack(side=tk.LEFT, padx=(6, 0))

        def refresh():
            # Apply current style changes to the module and refresh preview
            mod.style = s.copy()
            self._refresh_preview()

        def apply_and_close():
            s['radius'] = int(radius_var.get())
            s['padding'] = int(padding_var.get())
            mod.style = s
            top.destroy()
            self._refresh_preview()

        ttk.Button(top, text="应用", command=apply_and_close).pack(fill=tk.X, pady=(8, 0))

    def _open_theme_editor(self):
        top = tk.Toplevel(self.root)
        top.title("主题调色板")
        theme_id = self.theme_id.get()
        theme = dict(THEMES.get(theme_id, THEMES[DEFAULT_THEME_ID]))
        pal = dict(theme.get('palette', {}))
        bg_grad = dict(theme.get('background_gradient') or {}) if theme.get('background_gradient') else None

        def pick_palette(key, label):
            c = colorchooser.askcolor(title=f"选择 {label}")
            if c and c[1]:
                pal[key] = c[1]
                refresh()

        ttk.Button(top, text="背景纯色", command=lambda: pick_palette('background', '背景色')).pack(fill=tk.X)
        ttk.Button(top, text="文本颜色", command=lambda: pick_palette('text', '文本颜色')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="主色", command=lambda: pick_palette('primary', '主色')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="强调色", command=lambda: pick_palette('accent', '强调色')).pack(fill=tk.X, pady=(4, 0))

        def toggle_bg_gradient():
            nonlocal bg_grad
            if bg_grad:
                bg_grad = None
            else:
                bg_grad = {'start': pal.get('background', '#ffffff'), 'end': '#eaeaea', 'angle': 90}
            refresh()

        ttk.Button(top, text="切换背景渐变", command=toggle_bg_gradient).pack(fill=tk.X, pady=(4, 0))
        ang_var = tk.IntVar(value=int((bg_grad or {}).get('angle', 90)))
        ttk.Label(top, text="背景渐变角度(0/90)").pack(anchor='w', pady=(6, 0))
        ttk.Spinbox(top, from_=0, to=360, textvariable=ang_var).pack(fill=tk.X)

        def refresh():
            pass

        def apply_and_close():
            if 'custom' not in THEMES:
                THEMES['custom'] = dict(THEMES[DEFAULT_THEME_ID])
            THEMES['custom']['palette'] = pal
            if bg_grad:
                THEMES['custom']['background_gradient'] = {'start': bg_grad['start'], 'end': bg_grad['end'], 'angle': int(ang_var.get())}
            else:
                THEMES['custom'].pop('background_gradient', None)
            self.theme_id.set('custom')
            self._refresh_theme_values()
            top.destroy()
            self._refresh_preview()

        ttk.Button(top, text="应用", command=apply_and_close).pack(fill=tk.X, pady=(8, 0))

    def _choose_image(self, var: tk.StringVar):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.gif")])
        if p:
            var.set(p)

    def _pick_bg_color(self):
        c = colorchooser.askcolor(title="选择背景颜色")
        if c and c[1]:
            self.bg_color.set(c[1])
            self._refresh_preview()

    def _open_bg_editor(self):
        top = tk.Toplevel(self.root)
        top.title("背景渐变设置")
        grad = dict(self.bg_gradient or {}) if self.bg_gradient else None

        def toggle_grad():
            nonlocal grad
            if grad:
                grad = None
            else:
                grad = {'start': self.bg_color.get() or '#ffffff', 'end': '#eaeaea', 'angle': 90}

        def pick(which: str):
            nonlocal grad
            if not grad:
                messagebox.showinfo('渐变', '请先开启渐变后再选择颜色')
                return
            c = colorchooser.askcolor(title=f"选择{which}色")
            if c and c[1]:
                grad[which] = c[1]

        ttk.Button(top, text="切换渐变开关", command=toggle_grad).pack(fill=tk.X)
        ttk.Button(top, text="选择起始色", command=lambda: pick('start')).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(top, text="选择结束色", command=lambda: pick('end')).pack(fill=tk.X, pady=(4, 0))
        ang_var = tk.IntVar(value=int((grad or {}).get('angle', 90)))
        ttk.Label(top, text="角度(0/90)").pack(anchor='w', pady=(6, 0))
        ttk.Spinbox(top, from_=0, to=360, textvariable=ang_var).pack(fill=tk.X)

        def apply_and_close():
            if grad:
                grad['angle'] = int(ang_var.get())
            self.bg_gradient = grad
            top.destroy()
            self._refresh_preview()

        ttk.Button(top, text="应用", command=apply_and_close).pack(fill=tk.X, pady=(8, 0))


class _ScrollableFrame(ttk.Frame):
    def __init__(self, parent, padding=0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_propagate(False)
        # Canvas + Scrollbar + inner body frame
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vscroll.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.body = ttk.Frame(self.canvas, padding=padding)
        self.body_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        # Update scrollregion when body changes
        def _on_body_configure(_event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Keep the body width same as canvas width, but ensure minimum width
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:  # Only update if canvas has been properly sized
                self.canvas.itemconfigure(self.body_id, width=canvas_width)

        def _on_canvas_configure(_event=None):
            # Update body width when canvas is resized
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:
                self.canvas.itemconfigure(self.body_id, width=canvas_width)

        self.body.bind("<Configure>", _on_body_configure)
        self.canvas.bind("<Configure>", _on_canvas_configure)

        # Handle mouse wheel when cursor over the frame
        self.body.bind("<Enter>", lambda e: self._bind_mousewheel(True))
        self.body.bind("<Leave>", lambda e: self._bind_mousewheel(False))

    def _bind_mousewheel(self, bind: bool):
        if bind:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        # Windows uses delta/120 units
        delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")
