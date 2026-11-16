
import csv
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from database.database import Database
from core.fate_engine import FateEngine

# ============================================================
# AZRAEL v0.5
# DATA & SYSTEM
# ============================================================

APP_TITLE = "AZRAEL"
VERSION = "v0.5"

BG = "#08080D"
SIDEBAR = "#0D0D14"
CARD = "#12121B"
CARD_HOVER = "#181824"
BORDER = "#252533"

PURPLE = "#7C3AED"
PURPLE_HOVER = "#6D28D9"
BLUE = "#2563EB"
GREEN = "#22C55E"
RED = "#EF4444"
YELLOW = "#F59E0B"

TEXT = "#F5F5F7"
TEXT_MUTED = "#8B8B9A"

PRIORITIES = ["LOW", "NORMAL", "HIGH", "CRITICAL"]
STATUSES = ["ALL", "PENDING", "COMPLETED"]

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = os.path.join(BASE_DIR, "assets/azrael_logo.png")


class Toast(ctk.CTkToplevel):
    def __init__(self, parent, message, kind="info"):
        super().__init__(parent)

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        colors = {
            "success": GREEN,
            "error": RED,
            "warning": YELLOW,
            "info": PURPLE
        }

        accent = colors.get(kind, PURPLE)

        frame = ctk.CTkFrame(
            self,
            fg_color=CARD,
            border_width=1,
            border_color=accent,
            corner_radius=10
        )
        frame.pack(fill="both", expand=True)

        ctk.CTkFrame(
            frame,
            width=4,
            fg_color=accent,
            corner_radius=4
        ).pack(side="left", fill="y", padx=(0, 10), pady=8)

        ctk.CTkLabel(
            frame,
            text=message,
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
            padx=12,
            pady=10
        ).pack(side="left")

        self.update_idletasks()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()

        width = self.winfo_width()
        height = self.winfo_height()

        x = parent_x + parent_w - width - 24
        y = parent_y + 24

        self.geometry(f"+{x}+{y}")
        self.after(2600, self.destroy)


class AzraelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} {VERSION}")
        self.geometry("1280x820")
        self.minsize(1120, 720)
        self.configure(fg_color=BG)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.db = Database()

        self.current_page = None
        self.sort_by = "id"
        self.sort_descending = True

        self.pages = {}
        self.nav_buttons = {}

        self.build_layout()
        self.build_pages()

        self.show_page("dashboard")

        self.protocol("WM_DELETE_WINDOW", self.close_app)

    # ========================================================
    # HELPERS
    # ========================================================

    def toast(self, message, kind="info"):
        Toast(self, message, kind)

    def button(self, parent, text, command, width=130, fg=PURPLE):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=38,
            corner_radius=8,
            fg_color=fg,
            hover_color=PURPLE_HOVER if fg == PURPLE else fg,
            font=ctk.CTkFont(size=12, weight="bold")
        )

    def section_title(self, parent, title, subtitle=""):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", padx=28, pady=(24, 14))

        ctk.CTkLabel(
            wrapper,
            text=title,
            text_color=TEXT,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(
                wrapper,
                text=subtitle,
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=(4, 0))

        return wrapper

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # ========================================================
    # LAYOUT
    # ========================================================

    def build_layout(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=245,
            corner_radius=0,
            fg_color=SIDEBAR
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=BG
        )
        self.content.pack(side="left", fill="both", expand=True)

        self.build_sidebar()

    def build_sidebar(self):
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=205
        )
        logo_frame.pack(fill="x", padx=12, pady=(12, 0))
        logo_frame.pack_propagate(False)

        if os.path.exists(LOGO_PATH):
            try:
                image = Image.open(LOGO_PATH)
                self.logo_image = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(175, 175)
                )

                ctk.CTkLabel(
                    logo_frame,
                    text="",
                    image=self.logo_image
                ).pack(expand=True)

            except Exception:
                self.build_text_logo(logo_frame)
        else:
            self.build_text_logo(logo_frame)

        ctk.CTkLabel(
            self.sidebar,
            text="MISSION CONTROL",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(pady=(0, 14))

        nav_items = [
            ("dashboard", "⌂  Dashboard"),
            ("missions", "◈  Missions"),
            ("add", "+  New Mission"),
            ("history", "◷  History"),
            ("activity", "≡  Activity Log"),
            ("statistics", "▥  Statistics"),
            ("settings", "⚙  Settings"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                command=lambda k=key: self.show_page(k),
                width=205,
                height=40,
                corner_radius=7,
                anchor="w",
                fg_color="transparent",
                hover_color=CARD_HOVER,
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            btn.pack(padx=20, pady=3)
            self.nav_buttons[key] = btn

        spacer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        spacer.pack(fill="both", expand=True)

        status_box = ctk.CTkFrame(
            self.sidebar,
            fg_color=CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER
        )
        status_box.pack(fill="x", padx=18, pady=(0, 10))

        ctk.CTkLabel(
            status_box,
            text="●  SYSTEM ONLINE",
            text_color=GREEN,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            status_box,
            text=f"AZRAEL {VERSION}",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def build_text_logo(self, parent):
        ctk.CTkLabel(
            parent,
            text="AZRAEL",
            text_color=TEXT,
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(expand=True)

    # ========================================================
    # PAGE SYSTEM
    # ========================================================

    def build_pages(self):
        self.pages["dashboard"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["missions"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["add"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["history"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["activity"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["statistics"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )
        self.pages["settings"] = ctk.CTkFrame(
            self.content, fg_color=BG
        )

        self.build_dashboard_page()
        self.build_missions_page()
        self.build_add_page()
        self.build_history_page()
        self.build_activity_page()
        self.build_statistics_page()
        self.build_settings_page()

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()

        self.pages[name].pack(fill="both", expand=True)
        self.current_page = name

        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(
                    fg_color=PURPLE,
                    text_color=TEXT
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_MUTED
                )

        if name == "dashboard":
            self.refresh_dashboard()

        elif name == "missions":
            self.refresh_missions()

        elif name == "history":
            self.refresh_history()

        elif name == "activity":
            self.refresh_activity()

        elif name == "statistics":
            self.refresh_statistics()

    # ========================================================
    # DASHBOARD
    # ========================================================

    def build_dashboard_page(self):
        page = self.pages["dashboard"]

        self.section_title(
            page,
            "Dashboard",
            "AZRAEL mission control center"
        )

        self.dashboard_cards = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )
        self.dashboard_cards.pack(fill="x", padx=28)

        self.card_labels = {}

        cards = [
            ("TOTAL MISSIONS", "total", BLUE),
            ("PENDING", "pending", YELLOW),
            ("COMPLETED", "completed", GREEN),
            ("CRITICAL PENDING", "critical", RED),
        ]

        for title, key, color in cards:
            card = ctk.CTkFrame(
                self.dashboard_cards,
                fg_color=CARD,
                corner_radius=12,
                border_width=1,
                border_color=BORDER
            )
            card.pack(side="left", fill="x", expand=True, padx=5)

            ctk.CTkLabel(
                card,
                text=title,
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=10, weight="bold")
            ).pack(anchor="w", padx=18, pady=(16, 2))

            label = ctk.CTkLabel(
                card,
                text="0",
                text_color=color,
                font=ctk.CTkFont(size=30, weight="bold")
            )
            label.pack(anchor="w", padx=18, pady=(0, 16))

            self.card_labels[key] = label

        recent_box = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        recent_box.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=22
        )

        ctk.CTkLabel(
            recent_box,
            text="RECENT MISSIONS",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=18, pady=(16, 8))

        self.dashboard_recent = ctk.CTkScrollableFrame(
            recent_box,
            fg_color="transparent"
        )
        self.dashboard_recent.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_dashboard(self):
        stats = self.db.get_statistics()

        for key, label in self.card_labels.items():
            label.configure(text=str(stats[key]))

        self.clear_frame(self.dashboard_recent)

        missions = self.db.get_missions(
            sort_by="id",
            descending=True
        )[:8]

        if not missions:
            ctk.CTkLabel(
                self.dashboard_recent,
                text="No missions recorded.",
                text_color=TEXT_MUTED
            ).pack(pady=40)
            return

        for mission in missions:
            self.mission_row(
                self.dashboard_recent,
                mission,
                compact=True
            )

    # ========================================================
    # MISSIONS
    # ========================================================

    def build_missions_page(self):
        page = self.pages["missions"]

        self.section_title(
            page,
            "Missions",
            "Search, filter, sort and control mission records"
        )

        controls = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER
        )
        controls.pack(fill="x", padx=28, pady=(0, 12))

        self.search_var = tk.StringVar()

        self.search_entry = ctk.CTkEntry(
            controls,
            textvariable=self.search_var,
            placeholder_text="Search by name, notes or ID...",
            width=260,
            height=38
        )
        self.search_entry.pack(side="left", padx=(12, 6), pady=12)
        self.search_entry.bind(
            "<KeyRelease>", lambda event: self.refresh_missions())

        self.status_filter = ctk.CTkComboBox(
            controls,
            values=STATUSES,
            width=135,
            height=38,
            command=lambda _: self.refresh_missions()
        )
        self.status_filter.set("ALL")
        self.status_filter.pack(side="left", padx=6, pady=12)

        self.priority_filter = ctk.CTkComboBox(
            controls,
            values=["ALL"] + PRIORITIES,
            width=135,
            height=38,
            command=lambda _: self.refresh_missions()
        )
        self.priority_filter.set("ALL")
        self.priority_filter.pack(side="left", padx=6, pady=12)

        self.sort_combo = ctk.CTkComboBox(
            controls,
            values=["ID", "Name", "Age", "Priority", "Status", "Created"],
            width=125,
            height=38,
            command=self.change_sort
        )
        self.sort_combo.set("ID")
        self.sort_combo.pack(side="left", padx=6, pady=12)

        self.sort_button = self.button(
            controls,
            "DESC ↓",
            self.toggle_sort_direction,
            width=105,
            fg=BLUE
        )
        self.sort_button.pack(side="left", padx=6, pady=12)

        self.missions_count = ctk.CTkLabel(
            controls,
            text="0 records",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=11)
        )
        self.missions_count.pack(side="right", padx=16)

        self.missions_scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )
        self.missions_scroll.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 18)
        )

    def change_sort(self, value):
        mapping = {
            "ID": "id",
            "Name": "name",
            "Age": "age",
            "Priority": "priority",
            "Status": "status",
            "Created": "created_at"
        }

        self.sort_by = mapping[value]
        self.refresh_missions()

    def toggle_sort_direction(self):
        self.sort_descending = not self.sort_descending

        self.sort_button.configure(
            text="DESC ↓" if self.sort_descending else "ASC ↑"
        )

        self.refresh_missions()

    def refresh_missions(self):
        if not hasattr(self, "missions_scroll"):
            return

        self.clear_frame(self.missions_scroll)

        rows = self.db.get_missions(
            search=self.search_var.get(),
            status=self.status_filter.get(),
            priority=self.priority_filter.get(),
            sort_by=self.sort_by,
            descending=self.sort_descending
        )

        self.missions_count.configure(
            text=f"{len(rows)} records"
        )

        if not rows:
            ctk.CTkLabel(
                self.missions_scroll,
                text="No missions match the current filters.",
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=13)
            ).pack(pady=60)
            return

        for mission in rows:
            self.mission_row(
                self.missions_scroll,
                mission
            )

    def mission_row(self, parent, mission, compact=False):
        (
            mission_id,
            name,
            age,
            priority,
            status,
            risk,
            deadline,
            created_at,
            completed_at,
            notes
        ) = mission

        fate_score = FateEngine.calculate(
            priority,
            risk,
            deadline,
            status
        )

        fate_class = FateEngine.classification(fate_score)
        height = 74 if compact else 82

        row = ctk.CTkFrame(
            parent,
            height=height,
            fg_color=CARD,
            corner_radius=9,
            border_width=1,
            border_color=BORDER
        )
        row.pack(fill="x", padx=2, pady=5)
        row.pack_propagate(False)

        left = ctk.CTkFrame(
            row,
            fg_color="transparent"
        )
        left.pack(side="left", fill="both", expand=True, padx=14)

        ctk.CTkLabel(
            left,
            text=f"#{mission_id}  {name}",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(10, 0))

        ctk.CTkLabel(
            left,
            text=f"Age: {age}   •   Created: {created_at}",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10)
        ).pack(anchor="w", pady=(2, 0))

        colors = {
            "LOW": TEXT_MUTED,
            "NORMAL": BLUE,
            "HIGH": YELLOW,
            "CRITICAL": RED
        }

        ctk.CTkLabel(
            row,
            text=priority,
            text_color=colors.get(priority, TEXT),
            font=ctk.CTkFont(size=10, weight="bold"),
            width=90
        ).pack(side="left", padx=4)

        status_color = GREEN if status == "COMPLETED" else YELLOW

        ctk.CTkLabel(
            row,
            text=status,
            text_color=status_color,
            font=ctk.CTkFont(size=10, weight="bold"),
            width=90
        ).pack(side="left", padx=4)
        fate_color = (
            RED if fate_score >= 70
            else YELLOW if fate_score >= 50
            else GREEN
        )

        ctk.CTkLabel(
            row,
            text=f"{fate_score}  •  {fate_class}",
            text_color=fate_color,
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            width=140
        ).pack(
            side="left",
            padx=4
        )
        if not compact:
            self.button(
                row,
                "Details",
                lambda mid=mission_id: self.show_details(mid),
                width=75,
                fg=BLUE
            ).pack(side="left", padx=4)

            if status == "PENDING":
                self.button(
                    row,
                    "Complete",
                    lambda mid=mission_id: self.complete_mission(mid),
                    width=85,
                    fg=GREEN
                ).pack(side="left", padx=4)
            else:
                self.button(
                    row,
                    "Reopen",
                    lambda mid=mission_id: self.reopen_mission(mid),
                    width=75,
                    fg=YELLOW
                ).pack(side="left", padx=4)

            self.button(
                row,
                "Delete",
                lambda mid=mission_id: self.delete_mission(mid),
                width=65,
                fg=RED
            ).pack(side="left", padx=(4, 12))

    # ========================================================
    # ADD MISSION
    # ========================================================

    def build_add_page(self):

        page = self.pages["add"]

        self.section_title(
            page,
            "New Mission",
            "Create a new mission record"
        )

        box = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        box.pack(fill="x", padx=28, pady=10)


        form = ctk.CTkFrame(
            box,
            fg_color="transparent"
        )

        form.pack(fill="x", padx=25, pady=25)


        # NAME
        ctk.CTkLabel(
            form,
            text="NAME",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0,5))


        self.add_name = ctk.CTkEntry(
            form,
            placeholder_text="Person / mission name",
            height=40
        )

        self.add_name.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0,12),
            pady=(0,18)
        )


        # AGE
        ctk.CTkLabel(
            form,
            text="AGE",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=0, column=1, sticky="w", pady=(0,5))


        self.add_age = ctk.CTkEntry(
            form,
            placeholder_text="Age",
            height=40
        )

        self.add_age.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(0,18)
        )


        # PRIORITY
        ctk.CTkLabel(
            form,
            text="PRIORITY",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=2, column=0, sticky="w", pady=(0,5))


        self.add_priority = ctk.CTkComboBox(
            form,
            values=PRIORITIES,
            height=40
        )

        self.add_priority.set("NORMAL")

        self.add_priority.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=(0,12),
            pady=(0,18)
        )


        # NOTES
        ctk.CTkLabel(
            form,
            text="NOTES",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=2, column=1, sticky="w", pady=(0,5))


        self.add_notes = ctk.CTkEntry(
            form,
            placeholder_text="Optional notes",
            height=40
        )

        self.add_notes.grid(
            row=3,
            column=1,
            sticky="ew",
            pady=(0,18)
        )


        # RISK
        ctk.CTkLabel(
            form,
            text="RISK (0 - 100)",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=4, column=0, sticky="w", pady=(0,5))


        self.risk_entry = ctk.CTkEntry(
            form,
            placeholder_text="Example: 70",
            height=40
        )

        self.risk_entry.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=(0,12),
            pady=(0,18)
        )


       # DEADLINE

        ctk.CTkLabel(
            form,
            text="DEADLINE",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=4, column=1, sticky="w", pady=(0,5))


        self.deadline_var = ctk.StringVar(value="Tomorrow")

        self.deadline_menu = ctk.CTkOptionMenu(
            form,
            variable=self.deadline_var,
            values=[
                "Today",
                "Tomorrow",
                "This Week",
                "Next Week",
                "No Deadline"
            ],
            height=40
        )

        self.deadline_menu.grid(
            row=5,
            column=1,
            sticky="ew",
            pady=(0,18)
        )


        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)


        self.button(
            box,
            "CREATE MISSION",
            self.create_mission,
            width=180
        ).pack(
            anchor="w",
            padx=25,
            pady=(0,25)
        )

    def create_mission(self):

        name = self.add_name.get().strip()
        age = self.add_age.get().strip()
        priority = self.add_priority.get()
        notes = self.add_notes.get("1.0", "end").strip()

        if not name:
            self.show_error("Mission name is required.")
            return

        try:
            age = int(age)
        except ValueError:
            self.show_error("Age must be a number.")
            return

        try:
            risk = int(self.risk_entry.get().strip())
        except ValueError:
            self.show_error("Risk must be a number between 0 and 100.")
            return

        if not 0 <= risk <= 100:
            self.show_error("Risk must be between 0 and 100.")
            return

        deadline = self.deadline_entry.get().strip()

        if not deadline:
            deadline = None

        mission_id = self.db.create_mission(
            name=name,
            age=age,
            priority=priority,
            risk=risk,
            deadline=deadline,
            notes=notes
        )

        self.add_name.delete(0, "end")
        self.add_age.delete(0, "end")
        self.add_priority.set("NORMAL")
        self.risk_entry.delete(0, "end")
        self.deadline_entry.delete(0, "end")
        self.add_notes.delete("1.0", "end")

        self.toast(
            f"Mission #{mission_id} created.",
            "success"
        )

        self.show_page("missions")
    # ========================================================
    # DETAILS / EDIT
    # ========================================================

    def show_details(self, mission_id):
        mission = self.db.get_mission(mission_id)

        if not mission:
            self.toast("Mission not found.", "error")
            return

        (
            mid,
            name,
            age,
            priority,
            status,
            risk,
            deadline,
            created_at,
            completed_at,
            notes
        ) = mission

        window = ctk.CTkToplevel(self)
        window.title(f"Mission #{mid}")
        window.geometry("570x600")
        window.configure(fg_color=BG)
        window.grab_set()

        ctk.CTkLabel(
            window,
            text=f"MISSION #{mid}",
            text_color=TEXT,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=28, pady=(24, 4))

        ctk.CTkLabel(
            window,
            text="Mission details",
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=28, pady=(0, 18))

        details = [
            ("NAME", name),
            ("AGE", str(age)),
            ("PRIORITY", priority),
            ("STATUS", status),
            ("CREATED", created_at),
            ("COMPLETED", completed_at or "—"),
            ("NOTES", notes or "—")
        ]

        for label, value in details:
            row = ctk.CTkFrame(
                window,
                fg_color=CARD,
                corner_radius=8,
                border_width=1,
                border_color=BORDER
            )
            row.pack(fill="x", padx=28, pady=4)

            ctk.CTkLabel(
                row,
                text=label,
                width=100,
                anchor="w",
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=9, weight="bold")
            ).pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(
                row,
                text=value,
                anchor="w",
                text_color=TEXT
            ).pack(side="left", fill="x", expand=True, padx=5)

        buttons = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        buttons.pack(fill="x", padx=28, pady=22)

        self.button(
            buttons,
            "EDIT",
            lambda: [window.destroy(), self.edit_mission(mid)],
            width=100,
            fg=BLUE
        ).pack(side="left")

        self.button(
            buttons,
            "CLOSE",
            window.destroy,
            width=100,
            fg=CARD_HOVER
        ).pack(side="right")

    def edit_mission(self, mission_id):
        mission = self.db.get_mission(mission_id)

        if not mission:
            self.toast("Mission not found.", "error")
            return

        (
            mid,
            name,
            age,
            priority,
            status,
            risk,
            deadline,
            created_at,
            completed_at,
            notes
        ) = mission

        window = ctk.CTkToplevel(self)
        window.title(f"Edit Mission #{mid}")
        window.geometry("570x520")
        window.configure(fg_color=BG)
        window.grab_set()

        ctk.CTkLabel(
            window,
            text=f"EDIT MISSION #{mid}",
            text_color=TEXT,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=28, pady=(24, 18))

        form = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        form.pack(fill="x", padx=28)

        ctk.CTkLabel(
            form,
            text="NAME",
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        name_entry = ctk.CTkEntry(form, height=40)
        name_entry.insert(0, name)
        name_entry.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(
            form,
            text="AGE",
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        age_entry = ctk.CTkEntry(form, height=40)
        age_entry.insert(0, str(age))
        age_entry.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(
            form,
            text="PRIORITY",
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        priority_combo = ctk.CTkComboBox(
            form,
            values=PRIORITIES,
            height=40
        )
        priority_combo.set(priority)
        priority_combo.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(
            form,
            text="NOTES",
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        notes_entry = ctk.CTkEntry(form, height=40)
        notes_entry.insert(0, notes or "")
        notes_entry.pack(fill="x", pady=(4, 20))

        def save():
            new_name = name_entry.get().strip()
            new_age_text = age_entry.get().strip()
            new_priority = priority_combo.get()
            new_notes = notes_entry.get().strip()

            if not new_name:
                self.toast("Name is required.", "error")
                return

            try:
                new_age = int(new_age_text)
            except ValueError:
                self.toast("Age must be a number.", "error")
                return

            if new_age < 0 or new_age > 150:
                self.toast("Enter a valid age.", "error")
                return

            self.db.update_mission(
                mission_id,
                new_name,
                new_age,
                new_priority,
                new_notes
            )

            window.destroy()
            self.refresh_all()
            self.toast(
                f"Mission #{mission_id} updated.",
                "success"
            )

        self.button(
            window,
            "SAVE CHANGES",
            save,
            width=160
        ).pack(anchor="w", padx=28)

    def complete_mission(self, mission_id):
        if not messagebox.askyesno(
            "Complete Mission",
            f"Mark mission #{mission_id} as completed?"
        ):
            return

        self.db.complete_mission(mission_id)
        self.refresh_all()
        self.toast(
            f"Mission #{mission_id} completed.",
            "success"
        )

    def reopen_mission(self, mission_id):
        self.db.reopen_mission(mission_id)
        self.refresh_all()
        self.toast(
            f"Mission #{mission_id} reopened.",
            "warning"
        )

    def delete_mission(self, mission_id):
        if not messagebox.askyesno(
            "Delete Mission",
            f"Delete mission #{mission_id}?\nThis action cannot be undone."
        ):
            return

        self.db.delete_mission(mission_id)
        self.refresh_all()
        self.toast(
            f"Mission #{mission_id} deleted.",
            "success"
        )

    # ========================================================
    # HISTORY
    # ========================================================

    def build_history_page(self):
        page = self.pages["history"]

        self.section_title(
            page,
            "History",
            "Completed mission records"
        )

        self.history_scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )
        self.history_scroll.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 18)
        )

    def refresh_history(self):
        self.clear_frame(self.history_scroll)

        rows = self.db.get_history()

        if not rows:
            ctk.CTkLabel(
                self.history_scroll,
                text="No completed missions yet.",
                text_color=TEXT_MUTED
            ).pack(pady=60)
            return

        for row in rows:
            (
                mission_id,
                name,
                age,
                priority,
                created_at,
                completed_at,
                notes
            ) = row

            box = ctk.CTkFrame(
                self.history_scroll,
                fg_color=CARD,
                corner_radius=9,
                border_width=1,
                border_color=BORDER
            )
            box.pack(fill="x", pady=5)

            ctk.CTkLabel(
                box,
                text=f"#{mission_id}  {name}",
                text_color=TEXT,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", padx=16, pady=(12, 2))

            ctk.CTkLabel(
                box,
                text=(
                    f"Age: {age}   •   Priority: {priority}   •   "
                    f"Completed: {completed_at}"
                ),
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=10)
            ).pack(anchor="w", padx=16, pady=(0, 12))

    # ========================================================
    # ACTIVITY LOG
    # ========================================================

    def build_activity_page(self):
        page = self.pages["activity"]

        self.section_title(
            page,
            "Activity Log",
            "Audit trail of AZRAEL system actions"
        )

        top = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=10,
            border_width=1,
            border_color=BORDER
        )
        top.pack(fill="x", padx=28, pady=(0, 12))

        self.activity_limit = ctk.CTkComboBox(
            top,
            values=["50", "100", "200"],
            width=100,
            height=36,
            command=lambda _: self.refresh_activity()
        )
        self.activity_limit.set("100")
        self.activity_limit.pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(
            top,
            text="latest records",
            text_color=TEXT_MUTED
        ).pack(side="left")

        self.activity_scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent"
        )
        self.activity_scroll.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 18)
        )

    def refresh_activity(self):
        self.clear_frame(self.activity_scroll)

        logs = self.db.get_activity_logs(
            int(self.activity_limit.get())
        )

        if not logs:
            ctk.CTkLabel(
                self.activity_scroll,
                text="No activity yet.",
                text_color=TEXT_MUTED
            ).pack(pady=60)
            return

        for log in logs:
            (
                log_id,
                mission_id,
                action,
                description,
                created_at
            ) = log

            box = ctk.CTkFrame(
                self.activity_scroll,
                fg_color=CARD,
                corner_radius=8,
                border_width=1,
                border_color=BORDER
            )
            box.pack(fill="x", pady=4)

            ctk.CTkLabel(
                box,
                text=action,
                text_color=PURPLE,
                width=180,
                anchor="w",
                font=ctk.CTkFont(size=10, weight="bold")
            ).pack(side="left", padx=12, pady=12)

            ctk.CTkLabel(
                box,
                text=description or "—",
                text_color=TEXT,
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                box,
                text=created_at,
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=10)
            ).pack(side="right", padx=12)

    # ========================================================
    # STATISTICS
    # ========================================================

    def build_statistics_page(self):
        page = self.pages["statistics"]

        self.section_title(
            page,
            "Statistics",
            "Mission database analytics"
        )

        self.stats_box = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        self.stats_box.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(0, 18)
        )

    def refresh_statistics(self):
        self.clear_frame(self.stats_box)

        stats = self.db.get_statistics()

        ctk.CTkLabel(
            self.stats_box,
            text=f"Completion Rate  {stats['completion_rate']}%",
            text_color=TEXT,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=24, pady=(24, 8))

        progress = ctk.CTkProgressBar(
            self.stats_box,
            height=12,
            progress_color=PURPLE
        )
        progress.pack(fill="x", padx=24)
        progress.set(stats["completion_rate"] / 100)

        ctk.CTkLabel(
            self.stats_box,
            text="PRIORITY DISTRIBUTION",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="w", padx=24, pady=(28, 12))

        total = max(stats["total"], 1)

        for priority in PRIORITIES:
            count = stats["priorities"].get(priority, 0)

            row = ctk.CTkFrame(
                self.stats_box,
                fg_color="transparent"
            )
            row.pack(fill="x", padx=24, pady=5)

            ctk.CTkLabel(
                row,
                text=priority,
                width=90,
                anchor="w",
                text_color=TEXT
            ).pack(side="left")

            bar = ctk.CTkProgressBar(
                row,
                height=10,
                progress_color={
                    "CRITICAL": RED,
                    "HIGH": YELLOW,
                    "NORMAL": BLUE,
                    "LOW": TEXT_MUTED
                }[priority]
            )
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(count / total)

            ctk.CTkLabel(
                row,
                text=str(count),
                width=40,
                text_color=TEXT_MUTED
            ).pack(side="right")

    # ========================================================
    # SETTINGS / DATA SYSTEM
    # ========================================================

    def build_settings_page(self):
        page = self.pages["settings"]

        self.section_title(
            page,
            "Settings",
            "Appearance, data management and database tools"
        )

        appearance = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        appearance.pack(fill="x", padx=28, pady=(0, 12))

        ctk.CTkLabel(
            appearance,
            text="APPEARANCE",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=18, pady=(16, 10))

        appearance_row = ctk.CTkFrame(
            appearance,
            fg_color="transparent"
        )
        appearance_row.pack(fill="x", padx=18, pady=(0, 18))

        ctk.CTkLabel(
            appearance_row,
            text="Mode",
            text_color=TEXT_MUTED
        ).pack(side="left")

        self.appearance_combo = ctk.CTkComboBox(
            appearance_row,
            values=["Dark", "Light", "System"],
            width=120,
            command=self.change_appearance
        )
        self.appearance_combo.set(
            self.db.get_setting("appearance", "Dark")
        )
        self.appearance_combo.pack(side="left", padx=12)

        ctk.CTkLabel(
            appearance_row,
            text="Accent",
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(20, 0))

        self.accent_combo = ctk.CTkComboBox(
            appearance_row,
            values=["Purple", "Blue", "Green", "Red"],
            width=120,
            command=self.change_accent
        )
        self.accent_combo.set(
            self.db.get_setting("accent", "Purple")
        )
        self.accent_combo.pack(side="left", padx=12)

        data_box = ctk.CTkFrame(
            page,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        data_box.pack(fill="x", padx=28, pady=6)

        ctk.CTkLabel(
            data_box,
            text="DATA & SYSTEM",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            data_box,
            text="Export records, backup the SQLite database or restore a valid AZRAEL backup.",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=18, pady=(0, 14))

        data_buttons = ctk.CTkFrame(
            data_box,
            fg_color="transparent"
        )
        data_buttons.pack(fill="x", padx=18, pady=(0, 18))

        self.button(
            data_buttons,
            "EXPORT CSV",
            self.export_csv,
            width=125,
            fg=BLUE
        ).pack(side="left", padx=(0, 8))

        self.button(
            data_buttons,
            "EXPORT JSON",
            self.export_json,
            width=125,
            fg=PURPLE
        ).pack(side="left", padx=8)

        self.button(
            data_buttons,
            "BACKUP DB",
            self.backup_db,
            width=125,
            fg=GREEN
        ).pack(side="left", padx=8)

        self.button(
            data_buttons,
            "RESTORE DB",
            self.restore_db,
            width=125,
            fg=YELLOW
        ).pack(side="left", padx=8)

        danger = ctk.CTkFrame(
            page,
            fg_color="#160B0D",
            corner_radius=12,
            border_width=1,
            border_color="#3B171B"
        )
        danger.pack(fill="x", padx=28, pady=(12, 0))

        ctk.CTkLabel(
            danger,
            text="DANGER ZONE",
            text_color=RED,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            danger,
            text="This deletes every mission record. Activity logs are preserved.",
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=18, pady=(0, 12))

        self.button(
            danger,
            "CLEAR ALL MISSIONS",
            self.clear_database,
            width=175,
            fg=RED
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def change_appearance(self, value):
        ctk.set_appearance_mode(value)
        self.db.set_setting("appearance", value)
        self.toast("Appearance updated.", "success")

    def change_accent(self, value):
        colors = {
            "Purple": PURPLE,
            "Blue": BLUE,
            "Green": GREEN,
            "Red": RED
        }

        ctk.set_default_color_theme("blue")
        self.db.set_setting("accent", value)

        self.toast(
            f"Accent saved: {value}.",
            "success"
        )

    # ========================================================
    # EXPORT / BACKUP / RESTORE
    # ========================================================

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Missions as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        try:
            count = self.db.export_missions_csv(path)
            self.toast(
                f"Exported {count} missions.",
                "success"
            )
            self.refresh_activity()
        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                str(exc)
            )

    def export_json(self):
        path = filedialog.asksaveasfilename(
            title="Export Missions as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if not path:
            return

        try:
            count = self.db.export_missions_json(path)
            self.toast(
                f"Exported {count} missions.",
                "success"
            )
            self.refresh_activity()
        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                str(exc)
            )

    def backup_db(self):
        path = filedialog.asksaveasfilename(
            title="Backup AZRAEL Database",
            defaultextension=".db",
            filetypes=[("SQLite database", "*.db")]
        )

        if not path:
            return

        try:
            self.db.backup_database(path)
            self.toast(
                "Database backup created.",
                "success"
            )
            self.refresh_activity()
        except Exception as exc:
            messagebox.showerror(
                "Backup Error",
                str(exc)
            )

    def restore_db(self):
        path = filedialog.askopenfilename(
            title="Restore AZRAEL Database",
            filetypes=[
                ("SQLite database", "*.db"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        if not messagebox.askyesno(
            "Restore Database",
            "Restore this database?\n\n"
            "Current data will be replaced by the selected backup."
        ):
            return

        try:
            self.db.restore_database(path)
            self.refresh_all()
            self.refresh_activity()

            self.toast(
                "Database restored successfully.",
                "success"
            )

        except Exception as exc:
            messagebox.showerror(
                "Restore Error",
                str(exc)
            )

    def clear_database(self):
        if not messagebox.askyesno(
            "Clear Database",
            "Delete ALL missions?\n\n"
            "Activity logs will be preserved."
        ):
            return

        self.db.clear_missions()
        self.refresh_all()
        self.refresh_activity()

        self.toast(
            "All missions cleared.",
            "warning"
        )

    # ========================================================
    # REFRESH / CLOSE
    # ========================================================

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_missions()
        self.refresh_history()
        self.refresh_activity()
        self.refresh_statistics()

    def close_app(self):
        try:
            self.db.close()
        finally:
            self.destroy()


if __name__ == "__main__":
    app = AzraelApp()
    app.mainloop()
