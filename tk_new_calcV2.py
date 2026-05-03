import tkinter as tk
from tkinter import messagebox
import math
import sys

# -----------------------------
# Scientific Calculator using pure Tk (grid)
# - Single file, Python 3.8+
# - Safely evaluates expressions using ONLY names from math (+ a few helpers)
# - Features: history, function & constant inserter, degree helpers (sind, cosd, tand, asind, acosd, atand),
#             memory (MC/MR/M+/M-), keyboard support, resizable grid
# - Uses only tk widgets (no ttk) with custom-styled buttons (hover/pressed/raised)
# -----------------------------

def build_safe_namespace(use_degrees: bool = False):
    """Return a dict of allowed names for eval, based on math module.
    Adds handy aliases and degree-based trig helpers without mutating math.
    """
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}

    # Helpful aliases
    allowed.update({
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        "nan": math.nan,
        "ln": math.log,   # natural log alias
        "log10": math.log10,
        "sqrt": math.sqrt,
    })

    # Degree trig helpers (always available)
    allowed.update({
        "sind": lambda x: math.sin(math.radians(x)),
        "cosd": lambda x: math.cos(math.radians(x)),
        "tand": lambda x: math.tan(math.radians(x)),
        "asind": lambda x: math.degrees(math.asin(x)),
        "acosd": lambda x: math.degrees(math.acos(x)),
        "atand": lambda x: math.degrees(math.atan(x)),
    })

    # Optional: remap bare sin/cos/tan to degree-mode if enabled
    if use_degrees:
        allowed.update({
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x)),
        })

    return allowed


class ScientificCalculatorTk(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tk Scientific Calculator — full math module (pure tk)")
        self.geometry("1100x600")
        self.minsize(900, 520)

        # App palette
        self.colors = {
            "bg": "#f5f5f7",
            "panel": "#ffffff",
            "text": "#111",
            "muted": "#666",
            "border": "#c9ccd3",

            "btn_bg": "#e6e6e9",
            "btn_fg": "#111",
            "btn_hover": "#eeeeef",
            "btn_press": "#d7d7db",

            "primary_bg": "#2b6cb0",
            "primary_hover": "#2c5282",
            "primary_press": "#2a4365",
            "primary_fg": "#ffffff",

            "danger_bg": "#c53030",
            "danger_hover": "#9b2c2c",
            "danger_press": "#742a2a",
            "danger_fg": "#ffffff",
        }
        self.configure(bg=self.colors["bg"])

        # State
        self.deg_mode = tk.BooleanVar(value=False)
        self.memory_value = 0.0

        # Top-level grid weights
        for i in range(3):
            self.grid_columnconfigure(i, weight=1, uniform="cols")
        for r in range(6):
            self.grid_rowconfigure(r, weight=0)
        self.grid_rowconfigure(6, weight=1)  # main row grows

        self._build_display()
        self._build_keypad()
        self._build_side_panels()
        self._build_statusbar()
        self._bind_keys()

    # ---------------- Button factory (pure tk styling) ----------------
    def _make_button(self, parent, text, command=None, kind="default", font=("Segoe UI", 12), padx=12, pady=8):
        """
        kind: "default" | "primary" | "danger" | "tool"
        Builds a tk.Button with hover/press bindings and raised/sunken relief.
        """
        c = self.colors
        if kind == "primary":
            bg, fg = c["primary_bg"], c["primary_fg"]
            hover, press = c["primary_hover"], c["primary_press"]
        elif kind == "danger":
            bg, fg = c["danger_bg"], c["danger_fg"]
            hover, press = c["danger_hover"], c["danger_press"]
        elif kind == "tool":
            bg, fg = "#efefef", c["btn_fg"]
            hover, press = "#e8e8e8", "#dcdcdc"
        else:
            bg, fg = c["btn_bg"], c["btn_fg"]
            hover, press = c["btn_hover"], c["btn_press"]

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover,
            activeforeground=fg,
            relief="raised",
            bd=6,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2",
            highlightthickness=0
        )

        # Hover/press effects
        def on_enter(_): btn.configure(bg=hover)
        def on_leave(_): btn.configure(bg=bg)
        def on_press(_): btn.configure(relief="sunken", bg=press)
        def on_release(_): btn.configure(relief="raised", bg=hover)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<ButtonPress-1>", on_press)
        btn.bind("<ButtonRelease-1>", on_release)

        return btn

    # --- UI Builders ---------------------------------------------------------
    def _build_display(self):
        # Expression entry
        self.expr_var = tk.StringVar()
        top = tk.Frame(self, bg=self.colors["bg"])
        top.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))

        self.entry = tk.Entry(top, textvariable=self.expr_var, font=("Consolas", 16), bg="#ffffff", fg=self.colors["text"], bd=2, relief="groove")
        self.entry.pack(fill="x")
        self.entry.focus_set()

        # Toolbar row (mode + actions)
        tool = tk.Frame(self, bg=self.colors["bg"])
        tool.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        tool.grid_columnconfigure(10, weight=1)

        tk.Checkbutton(tool, text="Degrees", variable=self.deg_mode, bg=self.colors["bg"], command=self._update_mode_tip)\
            .grid(row=0, column=0, padx=(0, 10))

        self._make_button(tool, "=  Evaluate", self.evaluate, kind="tool", font=("Segoe UI", 11), padx=10, pady=5).grid(row=0, column=1, padx=4)
        self._make_button(tool, "Clear", self.clear, kind="tool", font=("Segoe UI", 11), padx=10, pady=5).grid(row=0, column=2, padx=4)
        self._make_button(tool, "Backspace", self.backspace, kind="tool", font=("Segoe UI", 11), padx=10, pady=5).grid(row=0, column=3, padx=4)

        # Vertical separator
        tk.Frame(tool, width=1, height=24, bg=self.colors["border"]).grid(row=0, column=4, padx=8)

        self._make_button(tool, "Copy Result", self.copy_result, kind="tool", font=("Segoe UI", 11), padx=10, pady=5).grid(row=0, column=5, padx=4)
        self._make_button(tool, "Paste", self.paste_clipboard, kind="tool", font=("Segoe UI", 11), padx=10, pady=5).grid(row=0, column=6, padx=4)

        # Vertical separator
        tk.Frame(tool, width=1, height=24, bg=self.colors["border"]).grid(row=0, column=7, padx=8)

        self._make_button(tool, "MC", self.mem_clear, kind="tool", font=("Segoe UI", 11), padx=8, pady=5).grid(row=0, column=8, padx=2)
        self._make_button(tool, "MR", self.mem_recall, kind="tool", font=("Segoe UI", 11), padx=8, pady=5).grid(row=0, column=9, padx=2)
        self._make_button(tool, "M+", lambda: self.mem_add(+1), kind="tool", font=("Segoe UI", 11), padx=8, pady=5).grid(row=0, column=10, padx=2)
        self._make_button(tool, "M-", lambda: self.mem_add(-1), kind="tool", font=("Segoe UI", 11), padx=8, pady=5).grid(row=0, column=11, padx=2)

        # Result label
        self.result_var = tk.StringVar(value="Result will appear here")
        res_wrap = tk.Frame(self, bg=self.colors["bg"])
        res_wrap.grid(row=2, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        tk.Label(res_wrap, textvariable=self.result_var, anchor="w", font=("Consolas", 14), bg=self.colors["bg"], fg=self.colors["text"])\
            .pack(fill="x")

    def _build_keypad(self):
        # Keypad frame (numbers/operators)
        pad = tk.Frame(self, bg=self.colors["panel"], bd=1, relief="solid", highlightthickness=0)
        pad.grid(row=3, column=0, rowspan=4, sticky="nsew", padx=(8, 4), pady=(0, 8))

        # Make it expand nicely
        for c in range(6):
            pad.grid_columnconfigure(c, weight=1, uniform="padc")
        for r in range(6):
            pad.grid_rowconfigure(r, weight=1)

        # Rows of buttons
        buttons = [
            ["7", "8", "9", "/", "//", "%"],
            ["4", "5", "6", "*", "**", "^"],
            ["1", "2", "3", "-", "(", ")"],
            ["0", ".", ",", "+", "[", "]"],
            ["//=", "**=", "^=", "=", "<-", "AC"],
        ]

        # Map for advanced meaning
        special_map = {
            "=": self.evaluate,
            "<-": self.backspace,
            "AC": self.clear,
            "^": lambda: self.insert_text("**"),
            ",": lambda: self.insert_text(", "),
            "//=": lambda: self.insert_text("//="),
            "**=": lambda: self.insert_text("**="),
            "^=": lambda: self.insert_text("**="),
        }

        # Apply default vs special styles
        for r, row in enumerate(buttons):
            for c, label in enumerate(row):
                if label in special_map:
                    cmd = special_map[label]
                else:
                    cmd = lambda t=label: self.insert_text(t)

                kind = "default"
                if label == "=":
                    kind = "primary"
                elif label == "AC":
                    kind = "danger"

                self._make_button(
                    pad, label, cmd, kind=kind, font=("Segoe UI", 13), padx=10, pady=10
                ).grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

        # Quick constants row
        consts = tk.Frame(self, bg=self.colors["panel"], bd=1, relief="solid")
        consts.grid(row=3, column=1, sticky="nsew", padx=(4, 4), pady=(0, 4))
        for i in range(3):
            consts.grid_columnconfigure(i, weight=1, uniform="constc")

        self._make_button(consts, "pi", lambda: self.insert_text("pi")).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self._make_button(consts, "e",  lambda: self.insert_text("e")).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        self._make_button(consts, "tau",lambda: self.insert_text("tau")).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        # History panel
        hist_frame = tk.LabelFrame(self, text="History (double-click to reuse)", bg=self.colors["bg"], fg=self.colors["text"])
        hist_frame.grid(row=4, column=1, rowspan=3, sticky="nsew", padx=(4, 4), pady=(4, 8))
        hist_frame.grid_rowconfigure(0, weight=1)
        hist_frame.grid_columnconfigure(0, weight=1)
        self.history = tk.Listbox(hist_frame, font=("Consolas", 12))
        self.history.grid(row=0, column=0, sticky="nsew")
        self.history.bind("<Double-Button-1>", self._history_reuse)
        hist_scroll = tk.Scrollbar(hist_frame, orient="vertical", command=self.history.yview)
        hist_scroll.grid(row=0, column=1, sticky="ns")
        self.history.configure(yscrollcommand=hist_scroll.set)

    def _build_side_panels(self):
        # Functions panel: all public callables from math
        fn_frame = tk.LabelFrame(self, text="math functions (click to insert)", bg=self.colors["bg"], fg=self.colors["text"])
        fn_frame.grid(row=3, column=2, rowspan=3, sticky="nsew", padx=(4, 8), pady=(0, 8))
        fn_frame.grid_rowconfigure(0, weight=1)
        fn_frame.grid_columnconfigure(0, weight=1)

        # Gather function names (sorted)
        self.fn_names = sorted([
            name for name, obj in math.__dict__.items()
            if not name.startswith("_") and callable(obj)
        ])
        # Also append degree helpers
        self.fn_names += ["sind", "cosd", "tand", "asind", "acosd", "atand", "ln", "log10", "sqrt"]
        self.fn_names = sorted(set(self.fn_names))

        self.fn_list = tk.Listbox(fn_frame, selectmode="browse", font=("Consolas", 12))
        for n in self.fn_names:
            self.fn_list.insert(tk.END, n)
        self.fn_list.grid(row=0, column=0, sticky="nsew")
        self.fn_list.bind("<<ListboxSelect>>", self._update_fn_doc)
        self.fn_list.bind("<Double-Button-1>", self._insert_selected_function)
        fn_scroll = tk.Scrollbar(fn_frame, orient="vertical", command=self.fn_list.yview)
        fn_scroll.grid(row=0, column=1, sticky="ns")
        self.fn_list.configure(yscrollcommand=fn_scroll.set)

        # Docstring preview
        self.doc_var = tk.StringVar(value="Select a function to see its doc…")
        tk.Label(fn_frame, textvariable=self.doc_var, wraplength=320, justify="left", bg=self.colors["bg"], fg=self.colors["muted"])\
            .grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6,0))

        # Constants panel: all public non-callables from math
        const_frame = tk.LabelFrame(self, text="math constants (double-click to insert)", bg=self.colors["bg"], fg=self.colors["text"])
        const_frame.grid(row=6, column=2, sticky="nsew", padx=(4, 8), pady=(0, 8))
        const_frame.grid_columnconfigure(0, weight=1)
        const_frame.grid_rowconfigure(0, weight=1)

        self.const_names = sorted([
            name for name, obj in math.__dict__.items()
            if not name.startswith("_") and not callable(obj)
        ] + ["pi", "e", "tau", "inf", "nan"])  # ensure these show

        self.const_list = tk.Listbox(const_frame, selectmode="browse", font=("Consolas", 12), height=6)
        for n in self.const_names:
            self.const_list.insert(tk.END, n)
        self.const_list.grid(row=0, column=0, sticky="nsew")
        self.const_list.bind("<Double-Button-1>", self._insert_selected_constant)
        cscroll = tk.Scrollbar(const_frame, orient="vertical", command=self.const_list.yview)
        cscroll.grid(row=0, column=1, sticky="ns")
        self.const_list.configure(yscrollcommand=cscroll.set)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=self.colors["bg"])
        bar.grid(row=7, column=0, columnspan=3, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        self.mode_tip = tk.StringVar()
        self._update_mode_tip()
        tk.Label(bar, textvariable=self.mode_tip, anchor="w", bg=self.colors["bg"], fg=self.colors["muted"])\
            .grid(row=0, column=0, sticky="ew", padx=8, pady=4)

    def _bind_keys(self):
        self.bind("<Return>", lambda e: self.evaluate())
        self.bind("<KP_Enter>", lambda e: self.evaluate())
        self.bind("<Escape>", lambda e: self.clear())
        self.bind("<BackSpace>", lambda e: self.backspace())

    # --- Actions --------------------------------------------------------------
    def insert_text(self, text: str):
        # Insert at cursor in the entry
        self.entry.insert(tk.INSERT, text)
        # If we inserted function parentheses, move cursor inside the parens
        if text.endswith("()"):
            self.entry.icursor(self.entry.index(tk.INSERT) - 1)

    def backspace(self):
        s = self.expr_var.get()
        if s:
            self.expr_var.set(s[:-1])

    def clear(self):
        self.expr_var.set("")
        self.result_var.set("Result will appear here")

    def copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.result_var.get())

    def paste_clipboard(self):
        try:
            clip = self.selection_get(selection='CLIPBOARD')
            self.insert_text(clip)
        except tk.TclError:
            pass

    def evaluate(self):
        expr = self.expr_var.get().strip()
        if not expr:
            return
        try:
            allowed = build_safe_namespace(use_degrees=self.deg_mode.get())
            result = eval(expr, {"__builtins__": {}}, allowed)
            if isinstance(result, float) and result == 0:
                result = 0.0  # coerce -0.0
            self.result_var.set(str(result))
            self._push_history(expr, result)
        except ZeroDivisionError:
            self.result_var.set("Error: division by zero")
        except Exception as ex:
            self.result_var.set(f"Error: {ex.__class__.__name__}: {ex}")

    def _push_history(self, expr, result):
        line = f"{expr} = {result}"
        self.history.insert(0, line)
        if self.history.size() > 200:
            self.history.delete(200, tk.END)

    def _history_reuse(self, event):
        sel = self.history.curselection()
        if not sel:
            return
        text = self.history.get(sel[0])
        if "=" in text:
            self.expr_var.set(text.split("=", 1)[0].strip())

    def mem_clear(self):
        self.memory_value = 0.0
        self._set_status("Memory cleared")

    def mem_recall(self):
        self.insert_text(str(self.memory_value))
        self._set_status(f"Recalled {self.memory_value}")

    def mem_add(self, sign=+1):
        try:
            val = float(self.result_var.get())
        except ValueError:
            self._set_status("No numeric result to store")
            return
        self.memory_value += sign * val
        self._set_status(f"Memory = {self.memory_value}")

    def _insert_selected_function(self, event=None):
        sel = self.fn_list.curselection()
        if not sel:
            return
        name = self.fn_list.get(sel[0])
        self.insert_text(f"{name}()")

    def _insert_selected_constant(self, event=None):
        sel = self.const_list.curselection()
        if not sel:
            return
        name = self.const_list.get(sel[0])
        self.insert_text(name)

    def _update_fn_doc(self, event=None):
        sel = self.fn_list.curselection()
        if not sel:
            return
        name = self.fn_list.get(sel[0])
        obj = getattr(math, name, None)
        if name in {"sind","cosd","tand","asind","acosd","atand"}:
            docs = {
                "sind": "sind(x): sin(x°) — x in degrees",
                "cosd": "cosd(x): cos(x°) — x in degrees",
                "tand": "tand(x): tan(x°) — x in degrees",
                "asind": "asind(x): arcsin(x) in degrees",
                "acosd": "acosd(x): arccos(x) in degrees",
                "atand": "atand(x): arctan(x) in degrees",
            }
            self.doc_var.set(docs[name])
        elif name in {"ln", "log10", "sqrt"}:
            expl = {
                "ln": "ln(x): natural logarithm (base e)",
                "log10": "log10(x): base-10 logarithm",
                "sqrt": "sqrt(x): square root",
            }
            self.doc_var.set(expl[name])
        else:
            doc = getattr(obj, "__doc__", None) or "(no docstring available)"
            first = doc.strip().split("\n")[0]
            self.doc_var.set(f"{name} — {first}")

    def _update_mode_tip(self):
        mode = "DEGREES" if self.deg_mode.get() else "RADIANS"
        self.mode_tip.set(f"Trig mode: {mode}. Use sind/cosd/tand or toggle Degrees to reinterpret sin/cos/tan.")

    def _set_status(self, text: str):
        self.mode_tip.set(text)
        self.after(2500, self._update_mode_tip)


if __name__ == "__main__":
    try:
        app = ScientificCalculatorTk()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror("Fatal Error", f"{exc.__class__.__name__}: {exc}")
        sys.exit(1)

