"""
Student Result Management System - modern desktop app
Python + CustomTkinter + SQLite

Install once:   pip install customtkinter
Run:            python result_app.py
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

DB_NAME = "results.db"
PASS_PERCENT = 40
NAVY, TEAL, AMBER, RED = "#14213d", "#0e9f8e", "#f2a93b", "#e5534b"
CARD = ("#ffffff", "#172038")          # (light, dark)
BG = ("#f3f6fb", "#0e1424")
INK = ("#14213d", "#e8ecf7")
MUTED = ("#6b7794", "#93a0c0")


# ---------------- Database ----------------
def db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY, name TEXT NOT NULL,
            course TEXT NOT NULL, semester INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, roll_no TEXT NOT NULL,
            subject TEXT NOT NULL, marks REAL NOT NULL, max_marks REAL NOT NULL DEFAULT 100,
            UNIQUE (roll_no, subject),
            FOREIGN KEY (roll_no) REFERENCES students(roll_no) ON DELETE CASCADE)""")


def grade_for(p):
    for limit, g in ((90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (50, "C"), (40, "D")):
        if p >= limit:
            return g
    return "F"


def calculate(roll):
    with db() as c:
        rows = c.execute("SELECT subject, marks, max_marks FROM marks WHERE roll_no=? ORDER BY subject",
                         (roll,)).fetchall()
    if not rows:
        return None
    total, mx = sum(r[1] for r in rows), sum(r[2] for r in rows)
    pct = total / mx * 100
    ok = all(m / x * 100 >= PASS_PERCENT for _, m, x in rows)
    return dict(rows=rows, total=total, max=mx, pct=pct, ok=ok, grade=grade_for(pct) if ok else "F")


def pick(pair):
    """Choose light/dark value from a (light, dark) pair based on current theme."""
    return pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0]


# ---------------- App ----------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Result Manager")
        self.geometry("1120x700")
        self.minsize(980, 620)
        self.configure(fg_color=BG)
        self.cur_roll = ""

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_sidebar()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

        self.pages = {}
        for name, builder in (("Dashboard", self.build_dashboard), ("Students", self.build_students),
                              ("Marks", self.build_marks)):
            page = ctk.CTkFrame(self.body, fg_color="transparent")
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page
            builder(page)
        self.show("Dashboard")

    # ---------- shared pieces ----------
    def build_sidebar(self):
        side = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=NAVY)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="Result Manager", font=("Segoe UI", 20, "bold"),
                     text_color="white").pack(anchor="w", padx=22, pady=(28, 2))
        ctk.CTkLabel(side, text="Student performance", font=("Segoe UI", 12),
                     text_color="#8f9bbd").pack(anchor="w", padx=22, pady=(0, 26))
        self.nav = {}
        for name, label in (("Dashboard", "Dashboard"), ("Students", "Students"), ("Marks", "Marks & report")):
            b = ctk.CTkButton(side, text=label, anchor="w", height=42, corner_radius=10,
                              font=("Segoe UI", 14, "bold"), fg_color="transparent",
                              hover_color="#22335c", text_color="#c5cde3",
                              command=lambda n=name: self.show(n))
            b.pack(fill="x", padx=14, pady=3)
            self.nav[name] = b
        self.theme_switch = ctk.CTkSwitch(side, text="Dark mode", text_color="#c5cde3",
                                          progress_color=TEAL, command=self.toggle_theme)
        self.theme_switch.pack(side="bottom", anchor="w", padx=22, pady=24)

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")
        self.refresh_all()

    def show(self, name):
        self.pages[name].tkraise()
        for n, b in self.nav.items():
            b.configure(fg_color=TEAL if n == name else "transparent",
                        text_color="white" if n == name else "#c5cde3")
        self.refresh_all()

    def header(self, parent, title, subtitle):
        ctk.CTkLabel(parent, text=title, font=("Segoe UI", 28, "bold"), text_color=INK).pack(anchor="w")
        ctk.CTkLabel(parent, text=subtitle, font=("Segoe UI", 13), text_color=MUTED).pack(anchor="w", pady=(0, 16))

    def card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16, **kw)

    def entry(self, parent, placeholder, width=150, **kw):
        return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, height=36, corner_radius=9, **kw)

    def button(self, parent, text, cmd, color=TEAL, width=110):
        return ctk.CTkButton(parent, text=text, command=cmd, width=width, height=36, corner_radius=9,
                             fg_color=color, hover_color=color, font=("Segoe UI", 13, "bold"))

    def apply_tree_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        bg, ink = pick(CARD), pick(INK)
        style.configure("M.Treeview", background=bg, fieldbackground=bg, foreground=ink,
                        rowheight=34, borderwidth=0, font=("Segoe UI", 11))
        style.configure("M.Treeview.Heading", background=pick(BG), foreground=pick(MUTED),
                        font=("Segoe UI", 10, "bold"), borderwidth=0, relief="flat")
        style.map("M.Treeview", background=[("selected", TEAL)], foreground=[("selected", "white")])

    def tree(self, parent, cols, widths, height=8):
        self.apply_tree_style()
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        t = ttk.Treeview(frame, columns=cols, show="headings", height=height, style="M.Treeview")
        for c, w in zip(cols, widths):
            t.heading(c, text=c)
            t.column(c, width=w, anchor="w" if w >= 150 else "center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=sb.set)
        t.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        t.tag_configure("fail", foreground=RED)
        return frame, t

    def refresh_all(self):
        self.apply_tree_style()  # re-apply table colours for the current theme
        self.load_dashboard()
        self.load_students()
        self.load_marks()

    # ---------- Dashboard ----------
    def build_dashboard(self, p):
        self.header(p, "Dashboard", "How the class is doing across all subjects.")
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x")
        self.stat = {}
        for i, (key, title, color) in enumerate((("avg", "Class average", TEAL), ("n", "Students with results", CARD),
                                                  ("pass", "Passed", CARD), ("top", "Topper", CARD))):
            row.grid_columnconfigure(i, weight=1, uniform="s")
            c = ctk.CTkFrame(row, fg_color=color, corner_radius=16)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            hero = key == "avg"
            ctk.CTkLabel(c, text=title, font=("Segoe UI", 12),
                         text_color="#d6f3ef" if hero else MUTED).pack(anchor="w", padx=18, pady=(16, 0))
            v = ctk.CTkLabel(c, text="-", font=("Segoe UI", 26, "bold"), text_color="white" if hero else INK)
            v.pack(anchor="w", padx=18, pady=(0, 16))
            self.stat[key] = v

        mid = ctk.CTkFrame(p, fg_color="transparent")
        mid.pack(fill="x", pady=14)
        mid.grid_columnconfigure(0, weight=3)
        mid.grid_columnconfigure(1, weight=2)
        c1, c2 = self.card(mid), self.card(mid)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        c2.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(c1, text="Grade distribution", font=("Segoe UI", 15, "bold"),
                     text_color=INK).pack(anchor="w", padx=18, pady=(14, 0))
        self.bars = tk.Canvas(c1, height=170, highlightthickness=0)
        self.bars.pack(fill="x", padx=18, pady=10)
        ctk.CTkLabel(c2, text="Pass rate", font=("Segoe UI", 15, "bold"),
                     text_color=INK).pack(anchor="w", padx=18, pady=(14, 0))
        self.ring = tk.Canvas(c2, height=170, highlightthickness=0)
        self.ring.pack(fill="x", padx=18, pady=10)

        lb = self.card(p)
        lb.pack(fill="both", expand=True)
        ctk.CTkLabel(lb, text="Leaderboard", font=("Segoe UI", 15, "bold"),
                     text_color=INK).pack(anchor="w", padx=18, pady=(14, 4))
        f, self.board = self.tree(lb, ("Rank", "Roll no", "Name", "Total", "Percent", "Grade", "Result"),
                                  (60, 110, 220, 110, 90, 70, 90), height=6)
        f.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def all_results(self):
        with db() as c:
            studs = c.execute("SELECT roll_no, name FROM students").fetchall()
        out = [(r, n, calculate(r)) for r, n in studs]
        return sorted([x for x in out if x[2]], key=lambda x: x[2]["pct"], reverse=True)

    def load_dashboard(self):
        res = self.all_results()
        n = len(res)
        passed = sum(1 for x in res if x[2]["ok"])
        self.stat["avg"].configure(text=f"{sum(x[2]['pct'] for x in res) / n:.1f}%" if n else "-")
        self.stat["n"].configure(text=str(n))
        self.stat["pass"].configure(text=f"{passed} / {n}")
        self.stat["top"].configure(text=res[0][1] if n else "-")

        # grade bars
        cv, bg = self.bars, pick(CARD)
        cv.configure(bg=bg)
        cv.delete("all")
        grades = ["A+", "A", "B+", "B", "C", "D", "F"]
        cnt = {g: 0 for g in grades}
        for x in res:
            cnt[x[2]["grade"]] += 1
        peak = max(1, *cnt.values())
        w = max(cv.winfo_width(), 420)
        slot = w / len(grades)
        for i, g in enumerate(grades):
            h = cnt[g] / peak * 110
            x0 = i * slot + slot * 0.2
            x1 = (i + 1) * slot - slot * 0.2
            cv.create_rectangle(x0, 135 - max(h, 4), x1, 135, fill=RED if g == "F" else TEAL, outline="")
            cv.create_text((x0 + x1) / 2, 125 - max(h, 4), text=str(cnt[g]), fill=pick(INK), font=("Segoe UI", 10, "bold"))
            cv.create_text((x0 + x1) / 2, 152, text=g, fill=pick(MUTED), font=("Segoe UI", 10))

        # pass ring
        rg = self.ring
        rg.configure(bg=bg)
        rg.delete("all")
        pr = passed / n * 100 if n else 0
        cx, cy, r = max(rg.winfo_width(), 300) / 2 - 40, 85, 62
        box = (cx - r, cy - r, cx + r, cy + r)
        rg.create_arc(*box, start=90, extent=-359.9, style="arc", outline=RED if n else pick(MUTED), width=16)
        if n and pr > 0:
            rg.create_arc(*box, start=90, extent=-3.599 * pr, style="arc", outline=TEAL, width=16)
        rg.create_text(cx, cy, text=f"{pr:.0f}%", fill=pick(INK), font=("Segoe UI", 20, "bold"))
        rg.create_oval(cx + 110, 62, cx + 120, 72, fill=TEAL, outline="")
        rg.create_text(cx + 128, 67, text=f"{passed} passed", anchor="w", fill=pick(MUTED), font=("Segoe UI", 11))
        rg.create_oval(cx + 110, 92, cx + 120, 102, fill=RED, outline="")
        rg.create_text(cx + 128, 97, text=f"{n - passed} failed", anchor="w", fill=pick(MUTED), font=("Segoe UI", 11))

        self.board.delete(*self.board.get_children())
        for i, (roll, name, r_) in enumerate(res, 1):
            self.board.insert("", "end", tags=("" if r_["ok"] else "fail",), values=(
                i, roll, name, f"{r_['total']:g}/{r_['max']:g}", f"{r_['pct']:.1f}%",
                r_["grade"], "PASS" if r_["ok"] else "FAIL"))

    # ---------- Students ----------
    def build_students(self, p):
        self.header(p, "Students", "Add a student, or select one to edit.")
        form = self.card(p)
        form.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(padx=16, pady=16, anchor="w")
        self.s_roll = self.entry(inner, "Roll no")
        self.s_name = self.entry(inner, "Full name", 220)
        self.s_course = self.entry(inner, "Course (BCA)", 120)
        self.s_sem = self.entry(inner, "Sem", 70)
        for w in (self.s_roll, self.s_name, self.s_course, self.s_sem):
            w.pack(side="left", padx=(0, 10))
        self.button(inner, "Add", self.add_student).pack(side="left", padx=(6, 6))
        self.button(inner, "Update", self.update_student, AMBER, 90).pack(side="left", padx=6)
        self.button(inner, "Delete", self.delete_student, RED, 90).pack(side="left", padx=6)

        box = self.card(p)
        box.pack(fill="both", expand=True)
        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))
        self.search = self.entry(top, "Search students...", 260)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self.load_students())
        f, self.s_tree = self.tree(box, ("Roll no", "Name", "Course", "Semester", "Subjects"),
                                   (110, 260, 120, 100, 100), height=10)
        f.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self.s_tree.bind("<<TreeviewSelect>>", self.on_student_select)
        self.s_tree.bind("<Double-1>", lambda e: self.open_marks())

    def set_entry(self, e, text):
        e.delete(0, "end")
        e.insert(0, str(text))

    def read_student(self):
        roll = self.s_roll.get().strip().upper()
        name = self.s_name.get().strip().title()
        course = self.s_course.get().strip().upper()
        sem = self.s_sem.get().strip()
        if not (roll and name and course and sem):
            messagebox.showwarning("Missing data", "Please fill in all fields.")
        elif not sem.isdigit() or not 1 <= int(sem) <= 12:
            messagebox.showwarning("Invalid semester", "Semester must be a number from 1 to 12.")
        else:
            return roll, name, course, int(sem)
        return None

    def add_student(self):
        d = self.read_student()
        if not d:
            return
        try:
            with db() as c:
                c.execute("INSERT INTO students VALUES (?,?,?,?)", d)
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "That roll number already exists.")
            return
        for e in (self.s_roll, self.s_name, self.s_course, self.s_sem):
            e.delete(0, "end")
        self.refresh_all()

    def update_student(self):
        d = self.read_student()
        if not d:
            return
        with db() as c:
            cur = c.execute("UPDATE students SET name=?, course=?, semester=? WHERE roll_no=?",
                            (d[1], d[2], d[3], d[0]))
        if cur.rowcount == 0:
            messagebox.showerror("Not found", "No student with that roll number.")
        self.refresh_all()

    def delete_student(self):
        roll = self.s_roll.get().strip().upper()
        if roll and messagebox.askyesno("Confirm", f"Delete {roll} and all their marks?"):
            with db() as c:
                c.execute("DELETE FROM students WHERE roll_no=?", (roll,))
            for e in (self.s_roll, self.s_name, self.s_course, self.s_sem):
                e.delete(0, "end")
            self.refresh_all()

    def on_student_select(self, _=None):
        sel = self.s_tree.selection()
        if sel:
            v = self.s_tree.item(sel[0])["values"]
            for e, val in zip((self.s_roll, self.s_name, self.s_course, self.s_sem), v[:4]):
                self.set_entry(e, val)

    def open_marks(self):
        sel = self.s_tree.selection()
        if sel:
            self.cur_roll = str(self.s_tree.item(sel[0])["values"][0])
            self.show("Marks")

    def load_students(self):
        term = f"%{self.search.get().strip()}%"
        with db() as c:
            rows = c.execute("""SELECT s.roll_no, s.name, s.course, s.semester,
                                (SELECT COUNT(*) FROM marks m WHERE m.roll_no = s.roll_no)
                                FROM students s WHERE s.roll_no LIKE ? OR s.name LIKE ? OR s.course LIKE ?
                                ORDER BY s.roll_no""", (term, term, term)).fetchall()
        self.s_tree.delete(*self.s_tree.get_children())
        for r in rows:
            self.s_tree.insert("", "end", values=r)

    # ---------- Marks ----------
    def build_marks(self, p):
        self.header(p, "Marks & report", "Pick a student and save subject marks. Saving an existing subject updates it.")
        form = self.card(p)
        form.pack(fill="x", pady=(0, 14))
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(padx=16, pady=16, anchor="w")
        self.student_menu = ctk.CTkOptionMenu(inner, values=["No students"], width=240, height=36,
                                              fg_color=TEAL, button_color=TEAL, command=self.on_pick_student)
        self.student_menu.pack(side="left", padx=(0, 10))
        self.m_subject = self.entry(inner, "Subject", 170)
        self.m_obt = self.entry(inner, "Marks", 80)
        self.m_max = self.entry(inner, "Max", 70)
        for w in (self.m_subject, self.m_obt, self.m_max):
            w.pack(side="left", padx=(0, 10))
        self.set_entry(self.m_max, 100)
        self.button(inner, "Save marks", self.save_marks).pack(side="left", padx=6)
        self.button(inner, "Remove", self.remove_subject, RED, 90).pack(side="left", padx=6)

        box = self.card(p)
        box.pack(fill="both", expand=True)
        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(14, 0))
        self.report_title = ctk.CTkLabel(top, text="Report card", font=("Segoe UI", 16, "bold"), text_color=INK)
        self.report_title.pack(side="left")
        self.button(top, "Export report", self.export_report, AMBER, 130).pack(side="right")
        f, self.m_tree = self.tree(box, ("Subject", "Obtained", "Max", "Percent"), (260, 110, 110, 110), height=7)
        f.pack(fill="both", expand=True, padx=14, pady=8)
        self.m_tree.bind("<<TreeviewSelect>>", self.on_mark_select)
        self.summary = ctk.CTkLabel(box, text="", font=("Segoe UI", 15, "bold"), text_color=INK)
        self.summary.pack(anchor="w", padx=18, pady=(0, 16))

    def on_pick_student(self, choice):
        self.cur_roll = choice.split(" - ")[0]
        self.load_marks()

    def on_mark_select(self, _=None):
        sel = self.m_tree.selection()
        if sel:
            sub, obt, mx, _ = self.m_tree.item(sel[0])["values"]
            self.set_entry(self.m_subject, sub)
            self.set_entry(self.m_obt, obt)
            self.set_entry(self.m_max, mx)

    def save_marks(self):
        subject = self.m_subject.get().strip().title()
        if not self.cur_roll or not subject:
            messagebox.showwarning("Missing data", "Choose a student and enter a subject.")
            return
        try:
            obt, mx = float(self.m_obt.get()), float(self.m_max.get())
        except ValueError:
            messagebox.showwarning("Invalid marks", "Marks must be numbers.")
            return
        if mx <= 0 or not 0 <= obt <= mx:
            messagebox.showwarning("Invalid marks", "Marks must be between 0 and the maximum marks.")
            return
        with db() as c:
            c.execute("""INSERT INTO marks (roll_no, subject, marks, max_marks) VALUES (?,?,?,?)
                         ON CONFLICT(roll_no, subject)
                         DO UPDATE SET marks=excluded.marks, max_marks=excluded.max_marks""",
                      (self.cur_roll, subject, obt, mx))
        self.m_subject.delete(0, "end")
        self.m_obt.delete(0, "end")
        self.refresh_all()

    def remove_subject(self):
        sel = self.m_tree.selection()
        if sel and self.cur_roll:
            sub = self.m_tree.item(sel[0])["values"][0]
            with db() as c:
                c.execute("DELETE FROM marks WHERE roll_no=? AND subject=?", (self.cur_roll, sub))
            self.refresh_all()
        else:
            messagebox.showinfo("Select subject", "Select a subject in the table first.")

    def load_marks(self):
        with db() as c:
            studs = c.execute("SELECT roll_no, name FROM students ORDER BY roll_no").fetchall()
        labels = [f"{r} - {n}" for r, n in studs] or ["No students"]
        self.student_menu.configure(values=labels)
        if self.cur_roll not in [r for r, _ in studs]:
            self.cur_roll = studs[0][0] if studs else ""
        current = next((l for l in labels if l.split(" - ")[0] == self.cur_roll), labels[0])
        self.student_menu.set(current)

        self.m_tree.delete(*self.m_tree.get_children())
        res = calculate(self.cur_roll) if self.cur_roll else None
        name = current.split(" - ", 1)[1] if " - " in current else ""
        self.report_title.configure(text=f"Report card: {name}" if name else "Report card")
        if not res:
            self.summary.configure(text="No marks yet. Save a subject above." if self.cur_roll else
                                   "Add a student first.", text_color=MUTED)
            return
        for sub, m, mx in res["rows"]:
            self.m_tree.insert("", "end", values=(sub, f"{m:g}", f"{mx:g}", f"{m / mx * 100:.1f}%"))
        self.summary.configure(
            text=f"Total {res['total']:g}/{res['max']:g}     {res['pct']:.2f}%     "
                 f"Grade {res['grade']}     {'PASS' if res['ok'] else 'FAIL'}",
            text_color=TEAL if res["ok"] else RED)

    def export_report(self):
        res = calculate(self.cur_roll) if self.cur_roll else None
        if not res:
            messagebox.showinfo("Nothing to export", "Select a student who has marks.")
            return
        with db() as c:
            name, course, sem = c.execute("SELECT name, course, semester FROM students WHERE roll_no=?",
                                          (self.cur_roll,)).fetchone()
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"report_{self.cur_roll}.txt",
                                            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        lines = ["=" * 52, "                 REPORT CARD", "=" * 52, f"Name     : {name}",
                 f"Roll No  : {self.cur_roll}", f"Course   : {course}    Semester: {sem}", "-" * 52,
                 f"{'Subject':<24}{'Marks':>10}{'Max':>8}{'%':>8}", "-" * 52]
        lines += [f"{s:<24}{m:>10g}{x:>8g}{m / x * 100:>8.1f}" for s, m, x in res["rows"]]
        lines += ["-" * 52, f"Total      : {res['total']:g} / {res['max']:g}",
                  f"Percentage : {res['pct']:.2f}%", f"Grade      : {res['grade']}",
                  f"Result     : {'PASS' if res['ok'] else 'FAIL'}", "=" * 52]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Exported", f"Report card saved to:\n{path}")


if __name__ == "__main__":
    init_db()
    app = App()
    app.after(150, app.refresh_all)   # redraw charts once the window has its real size
    app.mainloop()