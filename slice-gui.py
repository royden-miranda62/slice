import re
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import Calendar

# Set CustomTkinter theme and appearance mode
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def format_human_date(date_str):
    if not date_str or not str(date_str).strip():
        return ""
    s = str(date_str).strip()
    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "June",
        7: "July", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    m1 = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    if m1:
        y, m, d = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{d} {month_map[m]} {y}"
    m2 = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if m2:
        d, m, y = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{d} {month_map[m]} {y}"
    return s

def format_venue_date(venue, date_str):
    v = venue.strip() if venue else ""
    d = format_human_date(date_str) if date_str else ""
    if v and d:
        return f"{v} - {d}"
    elif v:
        return v
    elif d:
        return d
    return ""

# User Specification & PSD Extracted Color Palette & Constants
BG_COLOR = "#172a3b"
INPUT_BG = "#41596e"
BORDER_COLOR = "#ffffff"
TEXT_COLOR = "#ffffff"
MUTED_TEXT_COLOR = "#7f91a1"
HOVER_COLOR = "#526d85"
DISABLED_COLOR = "#2a3d4e"
DELETE_COLOR = "#ff5555"

CORNER_RADIUS = 8
INPUT_HEIGHT = 40
ROW_GAP = 10

# Exact PostScript Fonts Extracted from section mockups.psd
FONT_HEADER_FAMILY = "FatboldSlimRegular"
FONT_BODY_FAMILY = "AloeveraDisplay-Light"
FONT_REGULAR_FAMILY = "AloeveraDisplay-Regular"
FONT_ITALIC_FAMILY = "AloeveraDisplay-Lightitalic"
FONT_BLACK_FAMILY = "AloeveraDisplay-Black"


def get_header_font(size=60):
    return ctk.CTkFont(family=FONT_HEADER_FAMILY, size=size, weight="normal")


def get_body_font(size=14, weight="normal"):
    return ctk.CTkFont(family=FONT_BODY_FAMILY, size=size, weight=weight)


def get_label_font(size=16, weight="normal"):
    return ctk.CTkFont(family=FONT_REGULAR_FAMILY, size=size, weight=weight)


def get_subtitle_font(size=18, slant="italic"):
    return ctk.CTkFont(family=FONT_ITALIC_FAMILY, size=size, slant=slant)


def get_black_font(size=44):
    return ctk.CTkFont(family=FONT_BLACK_FAMILY, size=size, weight="normal")


class SliceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Slice - Bill Splitter")
        self.geometry("960x720")
        self.minsize(800, 600)
        self.configure(fg_color=BG_COLOR)

        # Global Application Data
        self.venue = ""
        self.date = ""
        self.people = []  # Sorted list of names
        self.payer = ""  # Selected payer
        self.menu_items = (
            []
        )  # List of dicts: {"name", "price", "qty", "total_price", "shared"}
        self.tax_amount = 0.0  # Float tax amount
        self.orders = {}  # Dict: person_name -> list of dicts [{"item_name", "qty"}]
        self.current_person_idx = 0  # Index for order stage navigation

        # Main Screen Container (Dynamic grid scaling)
        self.container = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.container.pack(fill="both", expand=True)

        self.show_screen("WelcomeScreen")

    def show_screen(self, screen_name):
        for widget in self.container.winfo_children():
            widget.destroy()

        if screen_name == "WelcomeScreen":
            screen = WelcomeScreen(self.container, self)
        elif screen_name == "PeopleScreen":
            screen = PeopleScreen(self.container, self)
        elif screen_name == "MenuScreen":
            screen = MenuScreen(self.container, self)
        elif screen_name == "OrderScreen":
            screen = OrderScreen(self.container, self)
        elif screen_name == "DisplayScreen":
            screen = DisplayScreen(self.container, self)
        else:
            return

        screen.pack(fill="both", expand=True)

    def calculate_bills(self):
        num_people = len(self.people)
        if num_people == 0:
            return {}, 0.0

        tax_per_person = self.tax_amount / num_people
        bills = {p: tax_per_person for p in self.people}

        total_ordered_qty = {m["name"]: 0 for m in self.menu_items}
        for person, order_list in self.orders.items():
            for item in order_list:
                iname = item["item_name"]
                iqty = item["qty"]
                if iname in total_ordered_qty:
                    total_ordered_qty[iname] += iqty

        for person, order_list in self.orders.items():
            for item in order_list:
                iname = item["item_name"]
                iqty = item["qty"]

                menu_item = next(
                    (m for m in self.menu_items if m["name"] == iname), None
                )
                if not menu_item or iqty <= 0:
                    continue

                if menu_item["shared"]:
                    tot_ord = total_ordered_qty[iname]
                    if tot_ord > 0:
                        unit_cost = menu_item["total_price"] / tot_ord
                        bills[person] += unit_cost * iqty
                else:
                    bills[person] += menu_item["price"] * iqty

        rounded_bills = {p: round(amt, 2) for p, amt in bills.items()}
        grand_total = round(sum(rounded_bills.values()), 2)
        return rounded_bills, grand_total


# ==========================================
# SCREEN 0: WELCOME / MAIN MENU
# ==========================================
class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, parent, app: SliceApp):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # Scrollable Frame for dynamic responsiveness
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Large Sliced Logo Title
        logo_label = ctk.CTkLabel(
            self.scroll_frame,
            text="SLICE",
            font=get_header_font(120),
            text_color=TEXT_COLOR,
        )
        logo_label.pack(pady=(40, 5))

        slogan_label = ctk.CTkLabel(
            self.scroll_frame,
            text="A user-friendly  bill splitter",
            font=get_subtitle_font(20, slant="italic"),
            text_color=TEXT_COLOR,
        )
        slogan_label.pack(pady=(0, 40))

        content_box = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        content_box.pack(fill="x", expand=True)

        # Venue Input
        venue_label = ctk.CTkLabel(
            content_box, text="Venue", font=get_label_font(18), text_color=TEXT_COLOR
        )
        venue_label.pack(pady=(10, 5))

        self.venue_entry = ctk.CTkEntry(
            content_box,
            placeholder_text="Venue",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=320,
            height=INPUT_HEIGHT,
            justify="center",
        )
        if self.app.venue:
            self.venue_entry.insert(0, self.app.venue)
        self.venue_entry.pack(pady=(0, 20))

        # Date Input with Calendar Menu Button
        date_label = ctk.CTkLabel(
            content_box, text="Date", font=get_label_font(18), text_color=TEXT_COLOR
        )
        date_label.pack(pady=(10, 5))

        date_frame = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        date_frame.pack(pady=(0, 20))

        self.date_entry = ctk.CTkEntry(
            date_frame,
            placeholder_text="Date (YYYY-MM-DD)",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=270,
            height=INPUT_HEIGHT,
            justify="center",
        )
        if self.app.date:
            self.date_entry.insert(0, self.app.date)
        self.date_entry.pack(side="left", padx=(0, 5))

        cal_btn = ctk.CTkButton(
            date_frame,
            text="📅",
            font=("Arial", 16),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=45,
            height=INPUT_HEIGHT,
            command=self.open_calendar_popup,
        )
        cal_btn.pack(side="left")

        # Navigation Footer
        nav_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        nav_frame.pack(fill="x", padx=40, pady=20, side="bottom")

        next_btn = ctk.CTkButton(
            nav_frame,
            text="NEXT",
            font=get_header_font(22),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=100,
            height=40,
            command=self.go_next,
        )
        next_btn.pack(side="right")

    def open_calendar_popup(self):
        top = ctk.CTkToplevel(self)
        top.title("Select Date")
        top.geometry("320x340")
        top.configure(fg_color=BG_COLOR)
        top.grab_set()

        cal = Calendar(
            top,
            selectmode="day",
            background=BG_COLOR,
            disabledbackground=BG_COLOR,
            bordercolor=BORDER_COLOR,
            headersbackground=INPUT_BG,
            headersforeground=TEXT_COLOR,
            selectbackground=MUTED_TEXT_COLOR,
            selectforeground=TEXT_COLOR,
            normalbackground=BG_COLOR,
            normalforeground=TEXT_COLOR,
            weekendbackground=BG_COLOR,
            weekendforeground=TEXT_COLOR,
            date_pattern="yyyy-mm-dd",
        )
        cal.pack(pady=15, padx=15, fill="both", expand=True)

        def set_date():
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, cal.get_date())
            top.destroy()

        confirm_btn = ctk.CTkButton(
            top,
            text="Select Date",
            font=get_label_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            height=35,
            command=set_date,
        )
        confirm_btn.pack(pady=(0, 15))

    def go_next(self):
        venue = self.venue_entry.get().strip()
        date_str = self.date_entry.get().strip()

        self.app.venue = venue
        self.app.date = date_str
        self.app.show_screen("PeopleScreen")


# ==========================================
# SCREEN 1: PEOPLE ("START THE PARTY")
# ==========================================
class PeopleScreen(ctk.CTkFrame):
    def __init__(self, parent, app: SliceApp):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # Static Header Title
        header_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        header_frame.pack(fill="x", padx=40, pady=(25, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="START THE PARTY",
            font=get_header_font(64),
            text_color=TEXT_COLOR,
        )
        title_label.pack(anchor="w")

        # Scrollable Content Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=(5, 5))

        content_box = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        content_box.pack(fill="x", expand=True)

        subtitle = ctk.CTkLabel(
            content_box,
            text="Add people to the split:",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        subtitle.pack(pady=(10, 15))

        # Dynamic People Inputs Container
        self.people_inputs_frame = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        self.people_inputs_frame.pack(fill="x", pady=5)

        self.person_entries = []

        initial_people = self.app.people if self.app.people else [""]
        for name in initial_people:
            self.add_person_entry(name)

        # Add Person Button
        add_btn = ctk.CTkButton(
            content_box,
            text="+ Add person",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=MUTED_TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=360,
            height=INPUT_HEIGHT,
            command=lambda: self.add_person_entry(""),
        )
        add_btn.pack(pady=12)

        # Who Paid Section
        who_paid_label = ctk.CTkLabel(
            content_box,
            text="Who paid?",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        who_paid_label.pack(pady=(20, 10))

        self.payer_var = ctk.StringVar(
            value=self.app.payer if self.app.payer else "Select"
        )
        self.payer_dropdown = ctk.CTkOptionMenu(
            content_box,
            variable=self.payer_var,
            values=["Select"],
            font=get_body_font(14),
            dropdown_font=get_body_font(14),
            fg_color=INPUT_BG,
            button_color=INPUT_BG,
            button_hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            dropdown_text_color=TEXT_COLOR,
            dropdown_fg_color=INPUT_BG,
            corner_radius=CORNER_RADIUS,
            width=360,
            height=INPUT_HEIGHT,
            dynamic_resizing=False,
        )
        self.payer_dropdown.pack(pady=5)
        self.update_dropdown_options()

        # Navigation Footer
        nav_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        nav_frame.pack(fill="x", padx=40, pady=15, side="bottom")

        prev_btn = ctk.CTkButton(
            nav_frame,
            text="PREV",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_prev,
        )
        prev_btn.pack(side="left")

        next_btn = ctk.CTkButton(
            nav_frame,
            text="NEXT",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_next,
        )
        next_btn.pack(side="right")

    def add_person_entry(self, default_text=""):
        row_idx = len(self.person_entries) + 1
        row_frame = ctk.CTkFrame(self.people_inputs_frame, fg_color=BG_COLOR)
        row_frame.pack(pady=ROW_GAP // 2)

        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="Name",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=360,
            height=INPUT_HEIGHT,
            justify="center",
        )
        if default_text:
            entry.insert(0, default_text)
        entry.pack(side="left", padx=(30, 5))
        entry.bind("<KeyRelease>", lambda e: self.update_dropdown_options())

        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            hover_color="#441111",
            text_color=BG_COLOR,
            width=25,
            height=INPUT_HEIGHT,
            corner_radius=4,
            command=lambda: self.remove_person_entry(row_frame, entry),
        )
        del_btn.pack(side="left", padx=2)

        def on_enter(e):
            del_btn.configure(text_color=DELETE_COLOR)

        def on_leave(e):
            del_btn.configure(text_color=BG_COLOR)

        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        entry.bind("<Enter>", on_enter)
        entry.bind("<Leave>", on_leave)
        del_btn.bind("<Enter>", on_enter)
        del_btn.bind("<Leave>", on_leave)

        self.person_entries.append(entry)
        self.update_dropdown_options()
        entry.focus()

    def remove_person_entry(self, row_frame, entry):
        if entry in self.person_entries:
            self.person_entries.remove(entry)
        row_frame.destroy()
        self.update_dropdown_options()

    def update_dropdown_options(self):
        if not hasattr(self, "payer_dropdown"):
            return
        names = []
        for entry in self.person_entries:
            val = entry.get().strip().title()
            if val and val not in names:
                names.append(val)
        names.sort()

        if not names:
            names = ["Select"]

        self.payer_dropdown.configure(values=names)

        current_val = self.payer_var.get()
        if current_val not in names:
            self.payer_var.set("Select")

    def go_prev(self):
        self.app.show_screen("WelcomeScreen")

    def go_next(self):
        names = []
        for entry in self.person_entries:
            val = entry.get().strip().title()
            if val:
                names.append(val)

        names = sorted(list(set(names)))
        if not names:
            messagebox.showerror("Error", "Please enter at least one person's name.")
            return

        payer = self.payer_var.get()
        if payer == "Select" or payer not in names:
            messagebox.showerror("Error", "Please select who paid for the bill.")
            return

        self.app.people = names
        self.app.payer = payer
        self.app.show_screen("MenuScreen")


# ==========================================
# SCREEN 2: MENU ("TONIGHT'S SPECIALS")
# ==========================================
class MenuScreen(ctk.CTkFrame):
    def __init__(self, parent, app: SliceApp):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # Static Header Title
        header_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        header_frame.pack(fill="x", padx=40, pady=(25, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="TONIGHT'S SPECIALS",
            font=get_header_font(58),
            text_color=TEXT_COLOR,
        )
        title_label.pack(anchor="w")

        # Scrollable Content Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=(5, 5))

        content_box = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        content_box.pack(fill="x", expand=True)

        subtitle = ctk.CTkLabel(
            content_box,
            text="Add items to the menu:",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        subtitle.pack(pady=(10, 15))

        # Column Headers
        headers_frame = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        headers_frame.pack(pady=5)

        lbl_name = ctk.CTkLabel(
            headers_frame,
            text="Name",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=260,
        )
        lbl_name.pack(side="left", padx=5)

        lbl_price = ctk.CTkLabel(
            headers_frame,
            text="Price",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=90,
        )
        lbl_price.pack(side="left", padx=5)

        lbl_qty = ctk.CTkLabel(
            headers_frame,
            text="Qty",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=70,
        )
        lbl_qty.pack(side="left", padx=5)

        lbl_shared = ctk.CTkLabel(
            headers_frame,
            text="Shared?",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=70,
        )
        lbl_shared.pack(side="left", padx=5)

        lbl_spacer = ctk.CTkLabel(headers_frame, text="", width=25)
        lbl_spacer.pack(side="left", padx=2)

        # Dynamic Item Rows Container
        self.items_container = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        self.items_container.pack(fill="x", pady=5)

        self.item_row_widgets = []

        initial_items = (
            self.app.menu_items
            if self.app.menu_items
            else [{"name": "", "price": "", "qty": "", "shared": False}]
        )
        for item in initial_items:
            self.add_item_row(item)

        # Add Item Button
        add_btn = ctk.CTkButton(
            content_box,
            text="+ Add item",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=MUTED_TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=510,
            height=INPUT_HEIGHT,
            command=lambda: self.add_item_row(),
        )
        add_btn.pack(pady=12)

        # Tax Section
        tax_label = ctk.CTkLabel(
            content_box,
            text="Enter tax amount:",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        tax_label.pack(pady=(20, 10))

        self.tax_entry = ctk.CTkEntry(
            content_box,
            placeholder_text="Amount",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=200,
            height=INPUT_HEIGHT,
            justify="center",
        )
        if self.app.tax_amount > 0:
            self.tax_entry.insert(0, str(self.app.tax_amount))
        self.tax_entry.pack(pady=5)

        # Navigation Footer
        nav_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        nav_frame.pack(fill="x", padx=40, pady=15, side="bottom")

        prev_btn = ctk.CTkButton(
            nav_frame,
            text="PREV",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_prev,
        )
        prev_btn.pack(side="left")

        next_btn = ctk.CTkButton(
            nav_frame,
            text="NEXT",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_next,
        )
        next_btn.pack(side="right")

    def add_item_row(self, item_data=None):
        row_idx = len(self.item_row_widgets) + 1
        row_frame = ctk.CTkFrame(self.items_container, fg_color=BG_COLOR)
        row_frame.pack(pady=ROW_GAP // 2)

        entry_name = ctk.CTkEntry(
            row_frame,
            placeholder_text=f"Item Name {row_idx}",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=260,
            height=INPUT_HEIGHT,
        )
        entry_name.pack(side="left", padx=5)

        entry_price = ctk.CTkEntry(
            row_frame,
            placeholder_text="Price",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=90,
            height=INPUT_HEIGHT,
            justify="center",
        )
        entry_price.pack(side="left", padx=5)

        entry_qty = ctk.CTkEntry(
            row_frame,
            placeholder_text="Qty",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=70,
            height=INPUT_HEIGHT,
            justify="center",
        )
        entry_qty.pack(side="left", padx=5)

        chk_shared = ctk.CTkCheckBox(
            row_frame,
            text="",
            fg_color=INPUT_BG,
            hover_color=HOVER_COLOR,
            border_color=BORDER_COLOR,
            border_width=1,
            checkmark_color=TEXT_COLOR,
            width=70,
        )
        chk_shared.pack(side="left", padx=5)

        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            hover_color="#441111",
            text_color=BG_COLOR,
            width=25,
            height=INPUT_HEIGHT,
            corner_radius=4,
            command=lambda: self.remove_item_row(row_frame, row_dict),
        )
        del_btn.pack(side="left", padx=2)

        if item_data:
            if item_data.get("name"):
                entry_name.insert(0, item_data["name"])
            if item_data.get("price") != "":
                entry_price.insert(0, str(item_data.get("price", "")))
            if item_data.get("qty") != "":
                entry_qty.insert(0, str(item_data.get("qty", "")))
            if item_data.get("shared", False):
                chk_shared.select()

        row_dict = {
            "row_frame": row_frame,
            "name": entry_name,
            "price": entry_price,
            "qty": entry_qty,
            "shared": chk_shared,
        }

        def on_enter(e):
            del_btn.configure(text_color=DELETE_COLOR)

        def on_leave(e):
            del_btn.configure(text_color=BG_COLOR)

        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        entry_name.bind("<Enter>", on_enter)
        entry_name.bind("<Leave>", on_leave)
        entry_price.bind("<Enter>", on_enter)
        entry_price.bind("<Leave>", on_leave)
        entry_qty.bind("<Enter>", on_enter)
        entry_qty.bind("<Leave>", on_leave)
        del_btn.bind("<Enter>", on_enter)
        del_btn.bind("<Leave>", on_leave)

        self.item_row_widgets.append(row_dict)
        entry_name.focus()

    def remove_item_row(self, row_frame, row_dict):
        if row_dict in self.item_row_widgets:
            self.item_row_widgets.remove(row_dict)
        row_frame.destroy()

    def go_prev(self):
        self.app.show_screen("PeopleScreen")

    def go_next(self):
        menu_items = []
        for row in self.item_row_widgets:
            name = row["name"].get().strip().title()
            price_str = row["price"].get().strip()
            qty_str = row["qty"].get().strip()
            shared = bool(row["shared"].get())

            if not name and not price_str and not qty_str:
                continue

            if not name or not price_str or not qty_str:
                messagebox.showerror(
                    "Error", "Please fill out all fields for added menu items."
                )
                return

            try:
                price = float(price_str)
                qty = int(qty_str)
                if price <= 0 or qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", f"Invalid price or quantity for item '{name}'."
                )
                return

            menu_items.append(
                {
                    "name": name,
                    "price": price,
                    "qty": qty,
                    "total_price": price * qty,
                    "shared": shared,
                }
            )

        if not menu_items:
            messagebox.showerror("Error", "Please add at least one menu item.")
            return

        tax_str = self.tax_entry.get().strip()
        tax_amount = 0.0
        if tax_str:
            try:
                tax_amount = float(tax_str)
                if tax_amount < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid tax amount.")
                return

        self.app.menu_items = menu_items
        self.app.tax_amount = tax_amount

        for person in self.app.people:
            if person not in self.app.orders:
                self.app.orders[person] = []

        self.app.current_person_idx = 0
        self.app.show_screen("OrderScreen")


# ==========================================
# SCREEN 3: ORDER ("ORDER UP!")
# ==========================================
class OrderScreen(ctk.CTkFrame):
    def __init__(self, parent, app: SliceApp):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # Static Header Title
        header_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        header_frame.pack(fill="x", padx=40, pady=(25, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="ORDER UP!",
            font=get_header_font(64),
            text_color=TEXT_COLOR,
        )
        title_label.pack(anchor="w")

        # Scrollable Content Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=(5, 5))

        columns_frame = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        columns_frame.pack(fill="both", expand=True, pady=5)

        # Left Column: Person Order Entry
        self.left_col = ctk.CTkFrame(columns_frame, fg_color=BG_COLOR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        current_person_name = self.app.people[self.app.current_person_idx]
        self.person_name_label = ctk.CTkLabel(
            self.left_col,
            text=f"{current_person_name}",
            font=get_label_font(20),
            text_color=TEXT_COLOR,
        )
        self.person_name_label.pack(pady=(0, 15))

        headers_frame = ctk.CTkFrame(self.left_col, fg_color=BG_COLOR)
        headers_frame.pack(pady=5)

        lbl_name = ctk.CTkLabel(
            headers_frame,
            text="Name",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=240,
        )
        lbl_name.pack(side="left", padx=5)

        lbl_qty = ctk.CTkLabel(
            headers_frame,
            text="Qty",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=80,
        )
        lbl_qty.pack(side="left", padx=5)

        lbl_spacer = ctk.CTkLabel(headers_frame, text="", width=25)
        lbl_spacer.pack(side="left", padx=2)

        self.order_rows_container = ctk.CTkFrame(self.left_col, fg_color=BG_COLOR)
        self.order_rows_container.pack(pady=5)

        # Right Column: Menu Summary Box
        self.right_col = ctk.CTkFrame(columns_frame, fg_color=BG_COLOR)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(20, 0))

        menu_summary_title = ctk.CTkLabel(
            self.right_col, text="Menu", font=get_label_font(20), text_color=TEXT_COLOR
        )
        menu_summary_title.pack(pady=(0, 15))

        summary_box = ctk.CTkFrame(
            self.right_col,
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            corner_radius=CORNER_RADIUS,
        )
        summary_box.pack(fill="both", expand=True, pady=5)

        menu_headers_frame = ctk.CTkFrame(summary_box, fg_color="transparent")
        menu_headers_frame.pack(fill="x", pady=8, padx=10)

        lbl_mname = ctk.CTkLabel(
            menu_headers_frame,
            text="Name",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=180,
            anchor="w",
        )
        lbl_mname.pack(side="left")

        lbl_mqty = ctk.CTkLabel(
            menu_headers_frame,
            text="Qty",
            font=get_body_font(14, "bold"),
            text_color=TEXT_COLOR,
            width=80,
            anchor="e",
        )
        lbl_mqty.pack(side="right")

        self.menu_summary_container = ctk.CTkFrame(summary_box, fg_color="transparent")
        self.menu_summary_container.pack(fill="both", expand=True, pady=5, padx=10)

        self.order_row_widgets = []
        self.load_person_order(current_person_name)

        # Add Order Item Button
        add_btn = ctk.CTkButton(
            self.left_col,
            text="+ Add item",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=MUTED_TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=350,
            height=INPUT_HEIGHT,
            command=lambda: self.add_order_row(),
        )
        add_btn.pack(pady=12)

        # Person Navigation Buttons (Prev / Next Person Order)
        person_nav_frame = ctk.CTkFrame(self.left_col, fg_color=BG_COLOR)
        person_nav_frame.pack(pady=10)

        self.prev_person_btn = ctk.CTkButton(
            person_nav_frame,
            text="Prev",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=80,
            height=35,
            command=self.prev_person,
        )
        self.prev_person_btn.pack(side="left", padx=5)

        self.next_person_btn = ctk.CTkButton(
            person_nav_frame,
            text="Next",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=80,
            height=35,
            command=self.next_person,
        )
        self.next_person_btn.pack(side="left", padx=5)

        self.update_menu_summary()
        self.update_person_nav_buttons()

        # Fixed Screen Navigation Footer
        nav_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        nav_frame.pack(fill="x", padx=40, pady=15, side="bottom")

        prev_screen_btn = ctk.CTkButton(
            nav_frame,
            text="PREV",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_prev_screen,
        )
        prev_screen_btn.pack(side="left")

        next_screen_btn = ctk.CTkButton(
            nav_frame,
            text="NEXT",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_next_screen,
        )
        next_screen_btn.pack(side="right")

    def load_person_order(self, person_name):
        for widget in self.order_rows_container.winfo_children():
            widget.destroy()
        self.order_row_widgets = []

        existing_orders = self.app.orders.get(person_name, [])
        if existing_orders:
            for item in existing_orders:
                self.add_order_row(item["item_name"], str(item["qty"]))
        else:
            self.add_order_row("", "")

    def add_order_row(self, selected_item="", default_qty=""):
        row_frame = ctk.CTkFrame(self.order_rows_container, fg_color=BG_COLOR)
        row_frame.pack(pady=ROW_GAP // 2)

        menu_names = [m["name"] for m in self.app.menu_items]
        dropdown_options = ["Select item"] + menu_names

        initial_val = selected_item if selected_item in menu_names else "Select item"
        item_var = ctk.StringVar(value=initial_val)

        dropdown = ctk.CTkOptionMenu(
            row_frame,
            variable=item_var,
            values=dropdown_options,
            font=get_body_font(14),
            dropdown_font=get_body_font(14),
            fg_color=INPUT_BG,
            button_color=INPUT_BG,
            button_hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            dropdown_text_color=TEXT_COLOR,
            dropdown_fg_color=INPUT_BG,
            corner_radius=CORNER_RADIUS,
            width=240,
            height=INPUT_HEIGHT,
            command=lambda v: self.update_menu_summary(),
        )
        dropdown.pack(side="left", padx=5)

        entry_qty = ctk.CTkEntry(
            row_frame,
            placeholder_text="Qty",
            font=get_body_font(14),
            fg_color=INPUT_BG,
            border_color=BORDER_COLOR,
            border_width=1,
            text_color=TEXT_COLOR,
            corner_radius=CORNER_RADIUS,
            width=80,
            height=INPUT_HEIGHT,
            justify="center",
        )
        if default_qty:
            entry_qty.insert(0, default_qty)
        entry_qty.pack(side="left", padx=5)
        entry_qty.bind("<KeyRelease>", lambda e: self.update_menu_summary())

        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            font=("Arial", 14, "bold"),
            fg_color="transparent",
            hover_color="#441111",
            text_color=BG_COLOR,
            width=25,
            height=INPUT_HEIGHT,
            corner_radius=4,
            command=lambda: self.remove_order_row(row_frame, row_dict),
        )
        del_btn.pack(side="left", padx=2)

        row_dict = {
            "row_frame": row_frame,
            "item_var": item_var,
            "qty_entry": entry_qty,
        }

        def on_enter(e):
            del_btn.configure(text_color=DELETE_COLOR)

        def on_leave(e):
            del_btn.configure(text_color=BG_COLOR)

        row_frame.bind("<Enter>", on_enter)
        row_frame.bind("<Leave>", on_leave)
        entry_qty.bind("<Enter>", on_enter)
        entry_qty.bind("<Leave>", on_leave)
        del_btn.bind("<Enter>", on_enter)
        del_btn.bind("<Leave>", on_leave)

        self.order_row_widgets.append(row_dict)
        self.update_menu_summary()
        dropdown.focus()

    def remove_order_row(self, row_frame, row_dict):
        if row_dict in self.order_row_widgets:
            self.order_row_widgets.remove(row_dict)
        row_frame.destroy()
        self.update_menu_summary()

    def save_current_person_order(self):
        current_person = self.app.people[self.app.current_person_idx]
        orders_list = []

        for row in self.order_row_widgets:
            iname = row["item_var"].get()
            qty_str = row["qty_entry"].get().strip()

            if iname == "Select item" and not qty_str:
                continue

            if iname == "Select item" or not qty_str:
                messagebox.showerror(
                    "Error", "Please select an item and enter quantity."
                )
                return False

            try:
                qty = int(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", f"Invalid quantity for item '{iname}'.")
                return False

            menu_item = next(
                (m for m in self.app.menu_items if m["name"] == iname), None
            )
            if not menu_item:
                continue

            orders_list.append({"item_name": iname, "qty": qty})

        self.app.orders[current_person] = orders_list
        return True

    def update_menu_summary(self):
        if not hasattr(self, "menu_summary_container"):
            return
        for widget in self.menu_summary_container.winfo_children():
            widget.destroy()

        total_ordered = {m["name"]: 0 for m in self.app.menu_items}

        for p_idx, person in enumerate(self.app.people):
            if p_idx == self.app.current_person_idx:
                for row in self.order_row_widgets:
                    iname = row["item_var"].get()
                    qty_str = row["qty_entry"].get().strip()
                    if iname != "Select item" and qty_str.isdigit():
                        total_ordered[iname] = total_ordered.get(iname, 0) + int(
                            qty_str
                        )
            else:
                for item in self.app.orders.get(person, []):
                    iname = item["item_name"]
                    total_ordered[iname] = total_ordered.get(iname, 0) + item["qty"]

        for idx, item in enumerate(self.app.menu_items, start=1):
            row_frame = ctk.CTkFrame(
                self.menu_summary_container, fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=3)

            name_text = f"{idx}. {item['name']}"
            lbl_name = ctk.CTkLabel(
                row_frame,
                text=name_text,
                font=get_body_font(13),
                text_color=TEXT_COLOR,
                anchor="w",
            )
            lbl_name.pack(side="left", padx=5)

            if item["shared"]:
                qty_text = f"{total_ordered.get(item['name'], 0)} (Shared)"
            else:
                rem_qty = max(0, item["qty"] - total_ordered.get(item["name"], 0))
                qty_text = f"{rem_qty}"

            lbl_qty = ctk.CTkLabel(
                row_frame,
                text=qty_text,
                font=get_body_font(13),
                text_color=TEXT_COLOR,
                anchor="e",
            )
            lbl_qty.pack(side="right", padx=5)

    def update_person_nav_buttons(self):
        if self.app.current_person_idx == 0:
            self.prev_person_btn.configure(state="disabled", fg_color=DISABLED_COLOR)
        else:
            self.prev_person_btn.configure(state="normal", fg_color=INPUT_BG)

        if self.app.current_person_idx == len(self.app.people) - 1:
            self.next_person_btn.configure(state="disabled", fg_color=DISABLED_COLOR)
        else:
            self.next_person_btn.configure(state="normal", fg_color=INPUT_BG)

    def prev_person(self):
        if self.save_current_person_order():
            if self.app.current_person_idx > 0:
                self.app.current_person_idx -= 1
                current_person = self.app.people[self.app.current_person_idx]
                self.person_name_label.configure(text=current_person)
                self.load_person_order(current_person)
                self.update_person_nav_buttons()

    def next_person(self):
        if self.save_current_person_order():
            if self.app.current_person_idx < len(self.app.people) - 1:
                self.app.current_person_idx += 1
                current_person = self.app.people[self.app.current_person_idx]
                self.person_name_label.configure(text=current_person)
                self.load_person_order(current_person)
                self.update_person_nav_buttons()

    def go_prev_screen(self):
        self.save_current_person_order()
        self.app.show_screen("MenuScreen")

    def go_next_screen(self):
        if self.save_current_person_order():
            self.app.show_screen("DisplayScreen")


# ==========================================
# SCREEN 4: DISPLAY ("THE SCORE'S SETTLED")
# ==========================================
class DisplayScreen(ctk.CTkFrame):
    def __init__(self, parent, app: SliceApp):
        super().__init__(parent, fg_color=BG_COLOR)
        self.app = app

        # Static Header Title
        header_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        header_frame.pack(fill="x", padx=40, pady=(25, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="THE SCORE'S SETTLED",
            font=get_header_font(58),
            text_color=TEXT_COLOR,
        )
        title_label.pack(anchor="w")

        # Scrollable Content Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG_COLOR)
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=(5, 5))

        content_box = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR)
        content_box.pack(fill="x", expand=True)

        # Centered Venue & Human-Readable Date Subheader
        venue_date_text = format_venue_date(self.app.venue, self.app.date)
        if venue_date_text:
            sub_info_label = ctk.CTkLabel(
                content_box,
                text=venue_date_text,
                font=get_label_font(18),
                text_color=TEXT_COLOR,
                justify="center",
            )
            sub_info_label.pack(pady=(10, 15))

        # Table Headers
        headers_frame = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        headers_frame.pack(pady=5)

        lbl_name = ctk.CTkLabel(
            headers_frame,
            text="Name",
            font=get_label_font(16),
            text_color=TEXT_COLOR,
            width=280,
        )
        lbl_name.pack(side="left", padx=5)

        lbl_amount = ctk.CTkLabel(
            headers_frame,
            text="Amount",
            font=get_label_font(16),
            text_color=TEXT_COLOR,
            width=120,
        )
        lbl_amount.pack(side="left", padx=5)

        # Calculate Payable Amounts
        bills, grand_total = self.app.calculate_bills()

        # Render Person Amount Rows
        rows_container = ctk.CTkFrame(content_box, fg_color=BG_COLOR)
        rows_container.pack(pady=5)

        for person, amt in bills.items():
            row_frame = ctk.CTkFrame(rows_container, fg_color=BG_COLOR)
            row_frame.pack(pady=ROW_GAP // 2)

            name_box = ctk.CTkLabel(
                row_frame,
                text=person,
                font=get_body_font(14),
                fg_color=INPUT_BG,
                corner_radius=CORNER_RADIUS,
                text_color=TEXT_COLOR,
                width=280,
                height=INPUT_HEIGHT,
            )
            name_box.pack(side="left", padx=5)

            amt_box = ctk.CTkLabel(
                row_frame,
                text=f"Rs. {amt:.2f}",
                font=get_body_font(14),
                fg_color=INPUT_BG,
                corner_radius=CORNER_RADIUS,
                text_color=TEXT_COLOR,
                width=120,
                height=INPUT_HEIGHT,
            )
            amt_box.pack(side="left", padx=5)

        # Grand Total Section
        total_label = ctk.CTkLabel(
            content_box,
            text="Total Amount",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        total_label.pack(pady=(20, 5))

        total_box = ctk.CTkLabel(
            content_box,
            text=f"Rs. {grand_total:.2f}",
            font=get_body_font(14, "bold"),
            fg_color=INPUT_BG,
            corner_radius=CORNER_RADIUS,
            text_color=TEXT_COLOR,
            width=200,
            height=INPUT_HEIGHT,
        )
        total_box.pack(pady=5)

        # Payer Message Section & Thank You Footer
        payer_msg_label = ctk.CTkLabel(
            content_box,
            text=f"Pay {self.app.payer}",
            font=get_label_font(18),
            text_color=TEXT_COLOR,
        )
        payer_msg_label.pack(pady=(25, 5))

        thank_you_label = ctk.CTkLabel(
            content_box,
            text="THANK YOU!",
            font=get_black_font(64),
            text_color=TEXT_COLOR,
        )
        thank_you_label.pack(pady=(5, 20))

        # Navigation Footer
        nav_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        nav_frame.pack(fill="x", padx=40, pady=15, side="bottom")

        prev_screen_btn = ctk.CTkButton(
            nav_frame,
            text="PREV",
            font=get_header_font(20),
            fg_color="transparent",
            hover_color=HOVER_COLOR,
            text_color=TEXT_COLOR,
            width=90,
            height=35,
            command=self.go_prev_screen,
        )
        prev_screen_btn.pack(side="left")

    def go_prev_screen(self):
        self.app.show_screen("OrderScreen")


if __name__ == "__main__":
    app = SliceApp()
    app.mainloop()
