import os
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

import messaging.send_message as send_message
import spam_detection.main as spam_detection
from user_auth.message_listener import listen_for_messages


class Theme:
    BG = "#07121f"
    SURFACE = "#0d1e32"
    SURFACE_ALT = "#112842"
    CARD = "#153353"
    CARD_HOVER = "#1a4067"
    TEXT = "#ecf4ff"
    MUTED = "#95aec9"
    ACCENT = "#18c4b3"
    ACCENT_HOVER = "#0ea99a"
    WARN = "#ef4444"
    BORDER = "#25486e"

    @staticmethod
    def font(size, weight="normal"):
        return ctk.CTkFont(family="Poppins", size=size, weight=weight)


def apply_gradient_background(parent, start=(7, 18, 31), end=(12, 32, 54)):
    canvas = tk.Canvas(parent, highlightthickness=0, bd=0)
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    canvas.lower("all")

    def draw(_event=None):
        canvas.delete("grad")
        w = parent.winfo_width()
        h = parent.winfo_height()
        if w <= 1 or h <= 1:
            return
        for x in range(w):
            t = x / max(1, (w - 1))
            r = int(start[0] + (end[0] - start[0]) * t)
            g = int(start[1] + (end[1] - start[1]) * t)
            b = int(start[2] + (end[2] - start[2]) * t)
            canvas.create_line(x, 0, x, h, fill=f"#{r:02x}{g:02x}{b:02x}", tags="grad")

    parent.bind("<Configure>", draw)
    draw()


def format_timestamp(ts):
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%d %b %H:%M")
    except Exception:
        return ""


class SplashScreen:
    def __init__(self, root, on_finish):
        self.root = root
        self.on_finish = on_finish

        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        apply_gradient_background(self.frame, start=(5, 14, 24), end=(11, 30, 48))

        self.logo = None
        if os.path.exists("assets/logo.png"):
            img = Image.open("assets/logo.png")
            self.logo = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))

        ctk.CTkLabel(self.frame, text="", image=self.logo, fg_color="transparent").pack(pady=(110, 16))
        ctk.CTkLabel(
            self.frame,
            text="Quantum Messaging",
            text_color=Theme.TEXT,
            font=Theme.font(24, "bold"),
        ).pack()
        ctk.CTkLabel(
            self.frame,
            text="OCR A-Level Computer Science NEA",
            text_color=Theme.MUTED,
            font=Theme.font(12),
        ).pack(pady=(6, 0))

        self.root.after(1400, self.close)

    def close(self):
        self.frame.destroy()
        self.on_finish()


class AuthOverlay:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success

        self.frame = ctk.CTkFrame(root, fg_color="transparent")
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        apply_gradient_background(self.frame, start=(5, 14, 24), end=(9, 24, 40))

        self.card = ctk.CTkFrame(
            self.frame,
            width=360,
            fg_color=Theme.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=Theme.BORDER,
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        self.status_label = ctk.CTkLabel(self.card, text="", text_color=Theme.MUTED, font=Theme.font(11))
        self.status_label.pack(side="bottom", pady=(0, 16))

        self.login_view = ctk.CTkFrame(self.card, fg_color="transparent")
        self.signup_view = ctk.CTkFrame(self.card, fg_color="transparent")
        self.build_login_view()
        self.build_signup_view()
        self.show_login_view()

    def _entry(self, master, placeholder, show=None):
        return ctk.CTkEntry(
            master,
            placeholder_text=placeholder,
            show=show,
            height=40,
            corner_radius=10,
            fg_color=Theme.SURFACE_ALT,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT,
        )

    def build_login_view(self):
        ctk.CTkLabel(self.login_view, text="RucksApp Login", text_color=Theme.TEXT, font=Theme.font(22, "bold")).pack(
            anchor="w", padx=18, pady=(18, 4)
        )
        ctk.CTkLabel(
            self.login_view,
            text="Sign in to access encrypted chats",
            text_color=Theme.MUTED,
            font=Theme.font(11),
        ).pack(anchor="w", padx=18, pady=(0, 10))

        self.email_entry = self._entry(self.login_view, "Email")
        self.email_entry.pack(fill="x", padx=18, pady=5)
        self.password_entry = self._entry(self.login_view, "Password", show="*")
        self.password_entry.pack(fill="x", padx=18, pady=5)

        ctk.CTkButton(
            self.login_view,
            text="Login",
            command=self.login,
            height=38,
            corner_radius=10,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#03221e",
            font=Theme.font(12, "bold"),
        ).pack(fill="x", padx=18, pady=(10, 5))

        ctk.CTkButton(
            self.login_view,
            text="Create Account",
            command=self.show_signup_view,
            height=34,
            corner_radius=10,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            font=Theme.font(12),
        ).pack(fill="x", padx=18, pady=(0, 14))

    def build_signup_view(self):
        ctk.CTkLabel(self.signup_view, text="Create Account", text_color=Theme.TEXT, font=Theme.font(22, "bold")).pack(
            anchor="w", padx=18, pady=(18, 4)
        )
        ctk.CTkLabel(
            self.signup_view,
            text="Enter email, password, first name and surname",
            text_color=Theme.MUTED,
            font=Theme.font(11),
        ).pack(anchor="w", padx=18, pady=(0, 10))

        self.signup_email_entry = self._entry(self.signup_view, "Email")
        self.signup_email_entry.pack(fill="x", padx=18, pady=4)
        self.signup_password_entry = self._entry(self.signup_view, "Password", show="*")
        self.signup_password_entry.pack(fill="x", padx=18, pady=4)
        self.signup_first_name_entry = self._entry(self.signup_view, "First name")
        self.signup_first_name_entry.pack(fill="x", padx=18, pady=4)
        self.signup_surname_entry = self._entry(self.signup_view, "Surname")
        self.signup_surname_entry.pack(fill="x", padx=18, pady=4)

        ctk.CTkButton(
            self.signup_view,
            text="Sign Up",
            command=self.register,
            height=38,
            corner_radius=10,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#03221e",
            font=Theme.font(12, "bold"),
        ).pack(fill="x", padx=18, pady=(10, 5))

        ctk.CTkButton(
            self.signup_view,
            text="Back to Login",
            command=self.show_login_view,
            height=34,
            corner_radius=10,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            font=Theme.font(12),
        ).pack(fill="x", padx=18, pady=(0, 14))

    def show_login_view(self):
        self.signup_view.pack_forget()
        self.login_view.pack(fill="both", expand=True)
        self.status_label.configure(text="")

    def show_signup_view(self):
        self.login_view.pack_forget()
        self.signup_view.pack(fill="both", expand=True)
        self.status_label.configure(text="")

    def login(self):
        from user_auth.auth_system import login as auth_login

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        uid, _token = auth_login(email, password)
        if uid:
            self.status_label.configure(text="Login successful", text_color="#22c55e")
            self.frame.destroy()
            self.on_success(uid)
        else:
            self.status_label.configure(text="Invalid login details", text_color=Theme.WARN)

    def register(self):
        from user_auth.auth_system import register as auth_register

        email = self.signup_email_entry.get().strip()
        password = self.signup_password_entry.get().strip()
        first_name = self.signup_first_name_entry.get().strip()
        surname = self.signup_surname_entry.get().strip()
        if not all([email, password, first_name, surname]):
            self.status_label.configure(text="All signup fields are required", text_color=Theme.WARN)
            return

        uid = auth_register(email, password, first_name, surname)
        if uid:
            self.status_label.configure(text="Account created. Please log in.", text_color="#22c55e")
            self.show_login_view()
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, email)
        else:
            self.status_label.configure(text="Registration failed", text_color=Theme.WARN)


class QuantumMessagingGUI:
    def __init__(self, root):
        self.root = root
        self.uid = None
        self.active_receiver = None
        self.active_receiver_name = ""
        self.user_map = {}
        self.listener_started = False

        self.profile_picture_path = ""
        self.profile_photo = None
        self.chat_icon = None
        self.avatar_cache = {}

        self.pages = {}
        self.nav_buttons = {}

        self.build_layout()

    # --------- Mobile shell ---------
    def build_layout(self):
        self.container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        apply_gradient_background(self.container)

        self.content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self.navbar = ctk.CTkFrame(
            self.container,
            fg_color=Theme.SURFACE,
            height=62,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER,
        )
        self.navbar.pack(fill="x", side="bottom")
        self.navbar.pack_propagate(False)

        self.build_pages()
        self.build_bottom_nav()
        self.show_page("chats")

    def build_bottom_nav(self):
        nav_items = [
            ("chats", "Chats"),
            ("contacts", "Contacts"),
            ("profile", "Profile"),
            ("settings", "Settings"),
        ]
        for idx in range(len(nav_items)):
            self.navbar.grid_columnconfigure(idx, weight=1, uniform="nav")

        for idx, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.navbar,
                text=label,
                command=lambda k=key: self.show_page(k),
                fg_color="transparent",
                hover_color=Theme.CARD,
                text_color=Theme.TEXT,
                corner_radius=10,
                height=40,
                width=72,
                font=Theme.font(11, "bold"),
            )
            btn.grid(row=0, column=idx, sticky="ew", padx=2, pady=10)
            self.nav_buttons[key] = btn

    def build_pages(self):
        self.pages["chats"] = self.build_chats_page()
        self.pages["contacts"] = self.build_contacts_page()
        self.pages["profile"] = self.build_profile_page()
        self.pages["settings"] = self.build_settings_page()

    # --------- Pages ---------
    def _build_mobile_header(self, parent, title, subtitle=""):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(header, text=title, text_color=Theme.TEXT, font=Theme.font(22, "bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, text_color=Theme.MUTED, font=Theme.font(11)).pack(anchor="w", pady=(2, 0))

    def build_chats_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")

        self.chat_list_view = ctk.CTkFrame(page, fg_color="transparent")
        self.chat_detail_view = ctk.CTkFrame(page, fg_color="transparent")

        # Chat list (mobile default)
        self._build_mobile_header(self.chat_list_view, "Chats", "Encrypted conversations")

        list_card = ctk.CTkFrame(
            self.chat_list_view,
            fg_color=Theme.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
        )
        list_card.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.chat_preview_frame = ctk.CTkScrollableFrame(
            list_card,
            fg_color="transparent",
            scrollbar_button_color=Theme.CARD,
            scrollbar_button_hover_color=Theme.CARD_HOVER,
        )
        self.chat_preview_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Chat detail (mobile full-screen flow)
        top = ctk.CTkFrame(self.chat_detail_view, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkButton(
            top,
            text="Back",
            command=self.show_chat_list,
            width=64,
            height=30,
            corner_radius=8,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            font=Theme.font(11, "bold"),
        ).pack(side="left")

        self.chat_avatar_label = ctk.CTkLabel(
            top,
            text="?",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=Theme.CARD,
            text_color=Theme.TEXT,
            font=Theme.font(12, "bold"),
        )
        self.chat_avatar_label.pack(side="left", padx=(10, 8))

        header_text = ctk.CTkFrame(top, fg_color="transparent")
        header_text.pack(side="left", fill="x", expand=True)

        self.chat_title = ctk.CTkLabel(header_text, text="Chat", text_color=Theme.TEXT, font=Theme.font(15, "bold"))
        self.chat_title.pack(anchor="w")

        self.chat_subtitle = ctk.CTkLabel(header_text, text="", text_color=Theme.MUTED, font=Theme.font(10))
        self.chat_subtitle.pack(anchor="w")

        self.message_scroll = ctk.CTkScrollableFrame(
            self.chat_detail_view,
            fg_color=Theme.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER,
            scrollbar_button_color=Theme.CARD,
            scrollbar_button_hover_color=Theme.CARD_HOVER,
        )
        self.message_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        spam_row = ctk.CTkFrame(self.chat_detail_view, fg_color="transparent")
        spam_row.pack(fill="x", padx=12, pady=(0, 4))

        self.spam_label = ctk.CTkLabel(spam_row, text="Spam probability: N/A", text_color=Theme.MUTED, font=Theme.font(10))
        self.spam_label.pack(side="left")

        self.spam_meter = ctk.CTkProgressBar(spam_row, width=108, progress_color=Theme.ACCENT, fg_color=Theme.CARD)
        self.spam_meter.pack(side="right")
        self.spam_meter.set(0)

        compose = ctk.CTkFrame(self.chat_detail_view, fg_color="transparent")
        compose.pack(fill="x", padx=12, pady=(2, 12))

        self.message_entry = ctk.CTkEntry(
            compose,
            placeholder_text="Type a message...",
            height=38,
            corner_radius=10,
            fg_color=Theme.SURFACE_ALT,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT,
        )
        self.message_entry.pack(side="left", fill="x", expand=True)
        self.message_entry.bind("<Return>", lambda _e: self.send_current_message())

        self.chat_icon = self._load_chat_icon()
        ctk.CTkButton(
            compose,
            text="Send",
            image=self.chat_icon,
            compound="left",
            command=self.send_current_message,
            width=86,
            height=38,
            corner_radius=10,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#03221e",
            font=Theme.font(11, "bold"),
        ).pack(side="left", padx=(8, 0))

        self.show_chat_list()
        return page

    def build_contacts_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")

        self._build_mobile_header(page, "Contacts", "Choose who to message")

        self.contact_search = ctk.CTkEntry(
            page,
            placeholder_text="Search by email",
            height=36,
            corner_radius=10,
            fg_color=Theme.SURFACE,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT,
        )
        self.contact_search.pack(fill="x", padx=12, pady=(0, 8))
        self.contact_search.bind("<KeyRelease>", lambda _e: self.load_contacts())

        self.contacts_scroll = ctk.CTkScrollableFrame(
            page,
            fg_color=Theme.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
            scrollbar_button_color=Theme.CARD,
            scrollbar_button_hover_color=Theme.CARD_HOVER,
        )
        self.contacts_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        return page

    def build_profile_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")

        self._build_mobile_header(page, "Profile", "Update account details")

        card = ctk.CTkFrame(
            page,
            fg_color=Theme.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
        )
        card.pack(fill="x", padx=12, pady=(0, 10))

        self.profile_image_label = ctk.CTkLabel(
            card,
            text="?",
            text_color=Theme.TEXT,
            fg_color=Theme.CARD,
            width=108,
            height=108,
            corner_radius=54,
            font=Theme.font(34, "bold"),
        )
        self.profile_image_label.pack(pady=(14, 8))

        ctk.CTkButton(
            card,
            text="Choose Picture",
            command=self.choose_profile_picture,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            corner_radius=10,
            height=32,
        ).pack(pady=(0, 10))

        self.display_name_entry = ctk.CTkEntry(
            card,
            placeholder_text="Display name",
            height=36,
            corner_radius=10,
            fg_color=Theme.SURFACE_ALT,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT,
        )
        self.display_name_entry.pack(fill="x", padx=12, pady=5)

        self.status_entry = ctk.CTkEntry(
            card,
            placeholder_text="Status",
            height=36,
            corner_radius=10,
            fg_color=Theme.SURFACE_ALT,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT,
        )
        self.status_entry.pack(fill="x", padx=12, pady=5)

        ctk.CTkButton(
            card,
            text="Save Profile",
            command=self.save_profile,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT_HOVER,
            text_color="#03221e",
            corner_radius=10,
            height=34,
            font=Theme.font(11, "bold"),
        ).pack(fill="x", padx=12, pady=(8, 12))

        self.profile_status_label = ctk.CTkLabel(card, text="", text_color=Theme.MUTED, font=Theme.font(11))
        self.profile_status_label.pack(pady=(0, 12))

        return page

    def build_settings_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")

        self._build_mobile_header(page, "Settings", "App controls")

        card = ctk.CTkFrame(
            page,
            fg_color=Theme.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
        )
        card.pack(fill="x", padx=12, pady=(0, 10))

        self.account_label = ctk.CTkLabel(card, text="Not logged in", text_color=Theme.MUTED, font=Theme.font(11))
        self.account_label.pack(anchor="w", padx=12, pady=(12, 8))

        ctk.CTkLabel(card, text="Appearance", text_color=Theme.TEXT, font=Theme.font(12, "bold")).pack(
            anchor="w", padx=12, pady=(0, 4)
        )
        mode_menu = ctk.CTkOptionMenu(
            card,
            values=["dark", "light", "system"],
            command=ctk.set_appearance_mode,
            fg_color=Theme.CARD,
            button_color=Theme.ACCENT,
            button_hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT,
            height=30,
        )
        mode_menu.set("dark")
        mode_menu.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            card,
            text="Refresh Contacts",
            command=self.load_contacts,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            corner_radius=10,
            height=32,
        ).pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(
            card,
            text="Refresh Conversations",
            command=self.load_conversation_previews,
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TEXT,
            corner_radius=10,
            height=32,
        ).pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(
            card,
            text="Log Out",
            command=self.logout,
            fg_color=Theme.WARN,
            hover_color="#dc2626",
            text_color="white",
            corner_radius=10,
            height=34,
            font=Theme.font(11, "bold"),
        ).pack(fill="x", padx=12, pady=(8, 12))

        return page

    # --------- Navigation ---------
    def show_page(self, page_name):
        for name, page in self.pages.items():
            page.pack_forget()
            self.nav_buttons[name].configure(fg_color="transparent")

        self.pages[page_name].pack(fill="both", expand=True)
        self.nav_buttons[page_name].configure(fg_color=Theme.CARD)

        if page_name == "contacts":
            self.load_contacts()
        elif page_name == "profile":
            self.load_profile()
        elif page_name == "chats":
            self.load_conversation_previews()
            if self.active_receiver:
                self.show_chat_detail()
            else:
                self.show_chat_list()

    def show_chat_list(self):
        self.chat_detail_view.pack_forget()
        self.chat_list_view.pack(fill="both", expand=True)
        if not self.active_receiver:
            self.chat_title.configure(text="Chat")
            self.chat_subtitle.configure(text="")
            self.chat_avatar_label.configure(
                image=None,
                text="?",
                fg_color=Theme.CARD,
                text_color=Theme.TEXT,
            )

    def show_chat_detail(self):
        self.chat_list_view.pack_forget()
        self.chat_detail_view.pack(fill="both", expand=True)

    # --------- Login transition ---------
    def init_after_login(self, uid):
        self.uid = uid
        user = self.get_user_record(uid)
        email = (user or {}).get("email", "")
        self.account_label.configure(text=f"Logged in: {email or (uid[:12] + '...')}")
        self.refresh_user_map()
        self.load_contacts()
        self.load_conversation_previews()
        self.start_listener_once()
        self.start_periodic_refresh()

    def get_user_record(self, uid):
        from user_auth.firebase_config import db

        try:
            record = db.child("users").child(uid).get()
            if record and record.val():
                return record.val()
        except Exception:
            return None
        return None

    def get_user_display_meta(self, uid, user_data=None):
        data = user_data or self.get_user_record(uid) or {}
        email = (data.get("email") or "").strip()
        first_name = (data.get("first_name") or "").strip()
        display_name = (data.get("display_name") or "").strip() or email or "Unknown User"
        initial = (data.get("profile_initial") or first_name[:1] or display_name[:1] or "?").upper()
        picture_path = (data.get("profile_picture") or "").strip()
        return {
            "uid": uid,
            "email": email,
            "display_name": display_name,
            "initial": initial,
            "profile_picture": picture_path,
        }

    def get_avatar_image(self, picture_path, size):
        if not picture_path or not os.path.exists(picture_path):
            return None
        key = (picture_path, size)
        cached = self.avatar_cache.get(key)
        if cached is not None:
            return cached
        try:
            img = Image.open(picture_path)
            avatar = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            self.avatar_cache[key] = avatar
            return avatar
        except Exception:
            return None

    def make_avatar_label(self, parent, user_meta, size=34):
        avatar_image = self.get_avatar_image(user_meta.get("profile_picture", ""), size)
        if avatar_image is not None:
            return ctk.CTkLabel(
                parent,
                text="",
                image=avatar_image,
                width=size,
                height=size,
                corner_radius=size // 2,
                fg_color=Theme.CARD,
            )
        return ctk.CTkLabel(
            parent,
            text=(user_meta.get("initial") or "?")[:1].upper(),
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=Theme.SURFACE_ALT,
            text_color=Theme.TEXT,
            font=Theme.font(max(10, size // 2), "bold"),
        )

    def set_chat_header_avatar(self, partner_uid):
        meta = self.get_user_display_meta(partner_uid)
        avatar_image = self.get_avatar_image(meta["profile_picture"], 30)
        if avatar_image is not None:
            self.chat_avatar_label.configure(text="", image=avatar_image, fg_color=Theme.CARD)
        else:
            self.chat_avatar_label.configure(
                image=None,
                text=meta["initial"],
                fg_color=Theme.SURFACE_ALT,
                text_color=Theme.TEXT,
            )

    # --------- Data loading ---------
    def refresh_user_map(self):
        from user_auth.firebase_config import db

        self.user_map = {}
        try:
            users = db.child("users").get()
            if users and users.val():
                for user in users.each():
                    data = user.val() or {}
                    self.user_map[user.key()] = data.get("display_name", data.get("email", "Unknown User"))
        except Exception:
            pass

    def load_contacts(self):
        from user_auth.firebase_config import db

        for widget in self.contacts_scroll.winfo_children():
            widget.destroy()

        if not self.uid:
            ctk.CTkLabel(self.contacts_scroll, text="Please log in first.", text_color=Theme.MUTED).pack(pady=12)
            return

        query = self.contact_search.get().strip().lower() if hasattr(self, "contact_search") else ""
        if not query:
            ctk.CTkLabel(
                self.contacts_scroll,
                text="Search by email to find a contact.",
                text_color=Theme.MUTED,
                font=Theme.font(11),
            ).pack(pady=14)
            return

        try:
            users = db.child("users").get()
        except Exception:
            users = None

        if not users or not users.val():
            ctk.CTkLabel(self.contacts_scroll, text="No contacts found.", text_color=Theme.MUTED).pack(pady=12)
            return

        shown = 0
        for user in users.each():
            partner_uid = user.key()
            if partner_uid == self.uid:
                continue

            data = user.val() or {}
            email = data.get("email", "").strip()
            if not email or query not in email.lower():
                continue

            display_name = data.get("display_name", email)
            status = data.get("status", "No status set")

            self.user_map[partner_uid] = display_name
            meta = self.get_user_display_meta(partner_uid, data)

            card = ctk.CTkFrame(
                self.contacts_scroll,
                fg_color=Theme.CARD,
                corner_radius=11,
                border_width=1,
                border_color=Theme.BORDER,
            )
            card.pack(fill="x", padx=6, pady=5)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 4))

            avatar = self.make_avatar_label(top_row, meta, size=34)
            avatar.pack(side="left")

            text_col = ctk.CTkFrame(top_row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

            ctk.CTkLabel(
                text_col, text=display_name, text_color=Theme.TEXT, font=Theme.font(12, "bold"), anchor="w"
            ).pack(fill="x")
            ctk.CTkLabel(text_col, text=email, text_color=Theme.MUTED, font=Theme.font(10), anchor="w").pack(fill="x")
            ctk.CTkLabel(text_col, text=status, text_color=Theme.MUTED, font=Theme.font(10), anchor="w").pack(fill="x")

            ctk.CTkButton(
                card,
                text="Message",
                command=lambda u=partner_uid: self.open_conversation(u),
                fg_color=Theme.SURFACE_ALT,
                hover_color=Theme.CARD_HOVER,
                text_color=Theme.TEXT,
                corner_radius=9,
                height=28,
                width=86,
                font=Theme.font(10, "bold"),
            ).pack(anchor="e", padx=10, pady=(0, 8))
            shown += 1

        if shown == 0:
            ctk.CTkLabel(self.contacts_scroll, text="No account found for that email.", text_color=Theme.MUTED).pack(
                pady=12
            )

    def open_conversation(self, partner_uid):
        self.active_receiver = partner_uid
        self.active_receiver_name = self.user_map.get(partner_uid, "Unknown User")
        self.chat_title.configure(text=self.active_receiver_name)
        self.chat_subtitle.configure(text=f"ID: {partner_uid[:10]}...")
        self.set_chat_header_avatar(partner_uid)
        self.show_page("chats")
        self.load_chat_history(partner_uid)
        self.show_chat_detail()

    def load_conversation_previews(self):
        from user_auth.firebase_config import db

        for widget in self.chat_preview_frame.winfo_children():
            widget.destroy()

        if not self.uid:
            ctk.CTkLabel(self.chat_preview_frame, text="Login to view chats", text_color=Theme.MUTED).pack(pady=12)
            return

        self.refresh_user_map()
        user_data_map = {}
        try:
            users = db.child("users").get()
            if users and users.val():
                for user in users.each():
                    user_data_map[user.key()] = user.val() or {}
        except Exception:
            user_data_map = {}

        try:
            chats = db.child("user_messages").child(self.uid).get()
        except Exception:
            chats = None

        if not chats or not chats.val():
            ctk.CTkLabel(self.chat_preview_frame, text="No conversations yet", text_color=Theme.MUTED).pack(pady=12)
            return

        previews = []
        for partner_uid, thread in chats.val().items():
            if not isinstance(thread, dict):
                continue
            latest = None
            for _msg_id, data in thread.items():
                ts = (data or {}).get("timestamp", 0)
                if latest is None or ts > latest.get("timestamp", 0):
                    latest = data
            if latest:
                previews.append(
                    (
                        latest.get("timestamp", 0),
                        partner_uid,
                        latest.get("message", ""),
                        latest.get("sender", ""),
                    )
                )

        previews.sort(key=lambda x: x[0], reverse=True)

        for ts, partner_uid, enc_msg, sender_uid in previews:
            snippet = self.decrypt_for_preview(enc_msg, sender_uid)
            user_data = user_data_map.get(partner_uid, {})
            meta = self.get_user_display_meta(partner_uid, user_data)
            name = meta["display_name"]

            card = ctk.CTkFrame(
                self.chat_preview_frame,
                fg_color=Theme.CARD,
                corner_radius=11,
                border_width=1,
                border_color=Theme.BORDER,
            )
            card.pack(fill="x", padx=6, pady=5)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=(8, 4))

            avatar = self.make_avatar_label(row, meta, size=34)
            avatar.pack(side="left")

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, padx=(8, 0))

            ctk.CTkLabel(text_col, text=name, text_color=Theme.TEXT, font=Theme.font(12, "bold"), anchor="w").pack(
                fill="x"
            )
            ctk.CTkLabel(text_col, text=snippet, text_color=Theme.MUTED, font=Theme.font(10), anchor="w").pack(
                fill="x"
            )
            ctk.CTkLabel(
                text_col, text=format_timestamp(ts), text_color=Theme.MUTED, font=Theme.font(9), anchor="w"
            ).pack(fill="x")

            ctk.CTkButton(
                card,
                text="Open",
                command=lambda u=partner_uid: self.open_conversation(u),
                fg_color=Theme.SURFACE_ALT,
                hover_color=Theme.CARD_HOVER,
                text_color=Theme.TEXT,
                corner_radius=9,
                width=70,
                height=26,
                font=Theme.font(10, "bold"),
            ).pack(anchor="e", padx=10, pady=(0, 8))

    def decrypt_for_preview(self, encrypted, sender_uid):
        if not encrypted or not self.uid:
            return ""
        try:
            key_owner = sender_uid or self.uid
            key = send_message.grab_symmetric_key(key_owner)
            text = send_message.decrypt_message(encrypted.encode(), key)
            return text[:36] + ("..." if len(text) > 36 else "")
        except Exception:
            return "[Encrypted message]"

    def clear_message_bubbles(self):
        for widget in self.message_scroll.winfo_children():
            widget.destroy()

    def scroll_messages_to_bottom(self):
        self.root.update_idletasks()
        if hasattr(self.message_scroll, "_parent_canvas"):
            self.message_scroll._parent_canvas.yview_moveto(1.0)

    def add_message_bubble(self, sender_label, text, stamp="", is_own=False, is_system=False):
        row = ctk.CTkFrame(self.message_scroll, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)

        if is_system:
            bubble = ctk.CTkLabel(
                row,
                text=text,
                text_color=Theme.MUTED,
                fg_color=Theme.SURFACE_ALT,
                corner_radius=10,
                font=Theme.font(10),
                padx=10,
                pady=6,
            )
            bubble.pack(anchor="center")
            return

        bubble_color = Theme.ACCENT if is_own else Theme.CARD
        text_color = "#03221e" if is_own else Theme.TEXT

        bubble = ctk.CTkFrame(row, fg_color=bubble_color, corner_radius=12)
        bubble.pack(anchor="e" if is_own else "w")

        ctk.CTkLabel(
            bubble,
            text=sender_label,
            text_color=text_color,
            font=Theme.font(9, "bold"),
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=10, pady=(6, 0))

        ctk.CTkLabel(
            bubble,
            text=text,
            text_color=text_color,
            font=Theme.font(11),
            anchor="w",
            justify="left",
            wraplength=240,
        ).pack(anchor="w", padx=10, pady=(0, 2))

        if stamp:
            ctk.CTkLabel(
                bubble,
                text=stamp,
                text_color=text_color,
                font=Theme.font(8),
                anchor="e",
            ).pack(anchor="e", padx=10, pady=(0, 6))

    def load_chat_history(self, other_uid):
        from user_auth.firebase_config import db

        self.clear_message_bubbles()

        if not self.uid:
            self.add_message_bubble("", "Please log in first.", is_system=True)
            return

        try:
            convo = db.child("user_messages").child(self.uid).child(other_uid).get()
        except Exception:
            convo = None

        if not convo or not convo.val():
            self.add_message_bubble("", "No messages yet.", is_system=True)
            return

        key_cache = {}

        def get_key_for_user(user_id):
            if not user_id:
                return None
            if user_id in key_cache:
                return key_cache[user_id]
            try:
                key_cache[user_id] = send_message.grab_symmetric_key(user_id)
            except Exception:
                key_cache[user_id] = None
            return key_cache[user_id]

        messages = []
        for _msg_id, data in convo.val().items():
            if isinstance(data, dict) and all(k in data for k in ("sender", "message", "timestamp")):
                messages.append(data)

        messages.sort(key=lambda m: m.get("timestamp", 0))

        for msg in messages:
            sender_label = "You" if msg.get("sender") == self.uid else (self.active_receiver_name or "Contact")
            stamp = format_timestamp(msg.get("timestamp", 0))

            text = "[Decryption failed]"
            sender_uid = msg.get("sender")
            key = get_key_for_user(sender_uid)
            if key:
                try:
                    text = send_message.decrypt_message(msg.get("message", "").encode(), key)
                except Exception:
                    pass

            self.add_message_bubble(
                sender_label=sender_label,
                text=text,
                stamp=stamp,
                is_own=(msg.get("sender") == self.uid),
                is_system=False,
            )

        self.scroll_messages_to_bottom()

    # --------- Messaging ---------
    def send_current_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        if not self.uid:
            self.show_system_message("[Error] Please log in first")
            return
        if not self.active_receiver:
            self.show_system_message("[Error] Select a contact first")
            return

        self.message_entry.delete(0, tk.END)

        spam_prob = float(spam_detection.get_spam_probability(message))
        self.spam_label.configure(text=f"Spam probability: {spam_prob:.3f}")
        self.spam_meter.set(max(0.0, min(1.0, spam_prob)))

        start = time.time()
        try:
            send_message.send_message(self.uid, self.active_receiver, message)
            elapsed = time.time() - start
            self.show_system_message(f"[RucksApp] Sent in {elapsed:.3f}s")
        except Exception as exc:
            self.show_system_message(f"[Error] Send failed: {exc}")

        self.load_chat_history(self.active_receiver)
        self.load_conversation_previews()

    def show_system_message(self, text):
        self.add_message_bubble("", text, is_system=True)
        self.scroll_messages_to_bottom()

    # --------- Listener and refresh ---------
    def start_listener_once(self):
        if self.listener_started or not self.uid:
            return
        self.listener_started = True

        def safe_callback(msg):
            self.root.after(0, lambda: self.on_incoming_message(msg))

        thread = threading.Thread(target=listen_for_messages, args=(self.uid, safe_callback), daemon=True)
        thread.start()

    def on_incoming_message(self, msg):
        sender = msg.get("sender")
        if sender == self.active_receiver:
            self.load_chat_history(self.active_receiver)
        self.load_conversation_previews()

    def start_periodic_refresh(self):
        def loop():
            if self.uid:
                self.load_conversation_previews()
                if self.active_receiver:
                    self.load_chat_history(self.active_receiver)
            self.root.after(2000, loop)

        loop()

    # --------- Profile ---------
    def choose_profile_picture(self):
        path = filedialog.askopenfilename(
            title="Choose profile picture",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")],
        )
        if not path:
            return
        self.profile_picture_path = path
        self.update_profile_image(path)

    def update_profile_image(self, path, initial="?"):
        if not path or not os.path.exists(path):
            self.profile_photo = None
            self.profile_image_label.configure(
                text=(initial or "?")[:1].upper(),
                image=None,
                text_color=Theme.TEXT,
                fg_color=Theme.CARD,
            )
            return
        try:
            img = Image.open(path)
            self.profile_photo = ctk.CTkImage(light_image=img, dark_image=img, size=(108, 108))
            self.profile_image_label.configure(text="", image=self.profile_photo)
        except Exception:
            self.profile_photo = None
            self.profile_image_label.configure(
                text=(initial or "?")[:1].upper(),
                image=None,
                text_color=Theme.TEXT,
                fg_color=Theme.CARD,
            )

    def load_profile(self):
        from user_auth.firebase_config import db

        if not self.uid:
            return

        user = self.get_user_record(self.uid)

        if not user:
            return

        self.display_name_entry.delete(0, tk.END)
        self.display_name_entry.insert(0, user.get("display_name", ""))

        self.status_entry.delete(0, tk.END)
        self.status_entry.insert(0, user.get("status", ""))

        self.profile_picture_path = user.get("profile_picture", "")
        initial = (user.get("profile_initial") or user.get("first_name", "")[:1] or user.get("email", "?")[:1]).upper()
        self.update_profile_image(self.profile_picture_path, initial=initial)

    def save_profile(self):
        from user_auth.firebase_config import db

        if not self.uid:
            return

        display_name = self.display_name_entry.get().strip()
        status = self.status_entry.get().strip()
        profile_initial = (display_name[:1] or "?").upper()

        try:
            db.child("users").child(self.uid).update(
                {
                    "display_name": display_name,
                    "status": status,
                    "profile_initial": profile_initial,
                    "profile_picture": self.profile_picture_path,
                }
            )
            self.profile_status_label.configure(text="Profile saved.", text_color="#22c55e")
            self.refresh_user_map()
            self.load_contacts()
            self.load_conversation_previews()
        except Exception as exc:
            self.profile_status_label.configure(text=f"Save failed: {exc}", text_color=Theme.WARN)

    # --------- Utilities ---------
    def _load_chat_icon(self):
        dark = "assets/chat_icon_dark.png"
        light = "assets/chat_icon_light.png"
        if os.path.exists(dark) and os.path.exists(light):
            dark_img = Image.open(dark)
            light_img = Image.open(light)
            return ctk.CTkImage(dark_image=dark_img, light_image=light_img, size=(15, 15))
        return None

    def logout(self):
        self.root.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("RucksApp - Quantum Messaging App")
    app.geometry("412x732")
    app.resizable(False, False)

    gui = QuantumMessagingGUI(app)

    def show_login():
        AuthOverlay(app, on_success=gui.init_after_login)

    SplashScreen(app, on_finish=show_login)
    app.mainloop()
