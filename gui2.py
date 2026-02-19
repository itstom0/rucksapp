# External imports
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import time
import threading
from PIL import Image  # using pillow package to display the splash screen image
import os

# Internal imports
import spam_detection.main as spam_detection
import messaging.send_message as send_message
from user_auth.message_listener import listen_for_messages


# ---------------------------------------
# LOGIN OVERLAY
# ---------------------------------------
def apply_gradient_to_frame(frame):
    canvas = tk.Canvas(frame, highlightthickness=0, bd=0)
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    canvas.lower("all")

    def draw_gradient(event=None):
        canvas.delete("grad")
        w = frame.winfo_width()
        h = frame.winfo_height()
        if w <= 1 or h <= 1:
            return
        start = (0x0f, 0x1c, 0x2e)
        end = (0x1b, 0xa3, 0x9c)
        steps = max(w, 1)
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = int(start[0] + (end[0] - start[0]) * t)
            g = int(start[1] + (end[1] - start[1]) * t)
            b = int(start[2] + (end[2] - start[2]) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(i, 0, i, h, fill=color, tags="grad")

    frame.bind("<Configure>", draw_gradient)
    draw_gradient()


class LoginOverlay:
    def __init__(self, parent, on_login_success):
        self.parent = parent
        self.on_login_success = on_login_success

        self.frame = ctk.CTkFrame(parent, fg_color="transparent", bg_color="transparent")
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)  # overlay whole window
        apply_gradient_to_frame(self.frame)

        title_font = ctk.CTkFont("Poppins", 20, "bold")
        body_font = ctk.CTkFont("Poppins", 12)

        ctk.CTkLabel(
            self.frame,
            text="RucksApp Login",
            font=title_font,
            text_color="#f8fafc",
            fg_color="transparent",
            bg_color="transparent"
        ).pack(pady=20)

        ctk.CTkLabel(
            self.frame,
            text="Email",
            font=body_font,
            text_color="#e2e8f0",
            fg_color="transparent",
            bg_color="transparent"
        ).pack()
        self.email_entry = ctk.CTkEntry(
            self.frame,
            width=260,
            height=36,
            fg_color="#0b1220",
            text_color="#f8fafc",
            border_color="#2dd4bf"
        )
        self.email_entry.pack(pady=6)

        ctk.CTkLabel(
            self.frame,
            text="Password",
            font=body_font,
            text_color="#e2e8f0",
            fg_color="transparent",
            bg_color="transparent"
        ).pack()
        self.password_entry = ctk.CTkEntry(
            self.frame,
            width=260,
            height=36,
            show="*",
            fg_color="#0b1220",
            text_color="#f8fafc",
            border_color="#2dd4bf"
        )
        self.password_entry.pack(pady=6)

        ctk.CTkButton(
            self.frame,
            text="Login",
            command=self.login,
            fg_color="#14b8a6",
            hover_color="#0d9488",
            text_color="#041014",
            width=200,
            height=38
        ).pack(pady=(12, 6))
        ctk.CTkButton(
            self.frame,
            text="Register",
            command=self.register,
            fg_color="#0b1220",
            hover_color="#111827",
            text_color="#f8fafc",
            width=200,
            height=34
        ).pack(pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.frame,
            text="",
            text_color="#f87171",
            fg_color="transparent",
            bg_color="transparent"
        )
        self.status_label.pack(pady=5)

    def login(self):
        from user_auth.auth_system import login as auth_login

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        uid, token = auth_login(email, password)
        if uid:
            self.status_label.configure(text="Login successful!", text_color="green")
            self.frame.destroy()  # remove overlay
            self.on_login_success(uid)  # continue with app
        else:
            self.status_label.configure(text="Invalid login. Try again.", text_color="red")

    def register(self):
        from user_auth.auth_system import register as auth_register

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        uid = auth_register(email, password)
        if uid:
            self.status_label.configure(text="Account created! Now log in.", text_color="green")
        else:
            self.status_label.configure(text="Registration failed.", text_color="red")


# ---------------------------------------
# SPLASH SCREEN
# ---------------------------------------
class SplashScreen:
    def __init__(self, parent, on_finish):
        self.parent = parent
        self.on_finish = on_finish

        self.frame = ctk.CTkFrame(parent, fg_color="transparent", bg_color="transparent")
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        apply_gradient_to_frame(self.frame)

        try:
            img = Image.open("assets/logo.png")
            self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 180))
            ctk.CTkLabel(
                self.frame,
                image=self.logo_img,
                text="",
                fg_color="transparent",
                bg_color="transparent"
            ).pack(pady=(90, 20))
        except Exception:
            ctk.CTkLabel(
                self.frame,
                text="RucksApp",
                font=("Helvetica", 24, "bold"),
                text_color="white",
                fg_color="transparent",
                bg_color="transparent"
            ).pack(pady=(120, 20))

        ctk.CTkLabel(
            self.frame,
            text="Welcome to RucksApp",
            font=ctk.CTkFont("Poppins", 13),
            text_color="#e2e8f0",
            fg_color="transparent",
            bg_color="transparent"
        ).pack()

        self.parent.after(1500, self.close)

    def close(self):
        self.frame.destroy()
        self.on_finish()


# ---------------------------------------
# MESSAGING GUI
# ---------------------------------------
class MessagingGUI:
    def __init__(self, root, uid=None):
        self.root = root
        self.uuid = uid
        self.active_receiver = None  # Will be set when user selects a contact
        self.active_receiver_name = None
        self.user_map = {}

        # UI styling (simple, consistent palette)
        self.ui = {
            "bg": "transparent",
            "surface": "#0b1220",
            "card": "#111827",
            "text": "#f8fafc",
            "muted": "#cbd5f5",
            "accent": "#14b8a6",
            "accent_hover": "#0d9488",
            "divider": "#1f334e"
        }
        self.fonts = {
            "title": ctk.CTkFont("Poppins", 18, "bold"),
            "heading": ctk.CTkFont("Poppins", 14, "bold"),
            "body": ctk.CTkFont("Poppins", 12),
            "small": ctk.CTkFont("Poppins", 10),
        }

        # Store frames (pages)
        # --------------------------
        self.pages = {}
        self.create_chats_page()
        self.create_contacts_page()
        self.create_profile_page()
        self.create_settings_page()
        self.create_navbar()

    # ---------------------------------------
    # INIT AFTER LOGIN
    # ---------------------------------------
    def init_after_login(self, uid):
        self.uuid = uid
        self.show_page("chats")
        self.show_chat_list()
        self.start_listener()
        self.start_chat_refresh()

    # ---------------------------------------
    # GRADIENT BACKGROUND
    # ---------------------------------------
    def apply_gradient(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0, bd=0)
        canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        canvas.lower("all")

        def draw_gradient(event=None):
            canvas.delete("grad")
            w = parent.winfo_width()
            h = parent.winfo_height()
            if w <= 1 or h <= 1:
                return
            start = (0x0f, 0x1c, 0x2e)
            end = (0x1b, 0xa3, 0x9c)
            steps = max(w, 1)
            for i in range(steps):
                t = i / (steps - 1) if steps > 1 else 0
                r = int(start[0] + (end[0] - start[0]) * t)
                g = int(start[1] + (end[1] - start[1]) * t)
                b = int(start[2] + (end[2] - start[2]) * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_line(i, 0, i, h, fill=color, tags="grad")

        parent.bind("<Configure>", draw_gradient)
        draw_gradient()

    # ---------------------------------------
    # OPEN CONVERSATION
    # ---------------------------------------
    def open_conversation(self, uid):
        self.set_active_receiver(uid)
        self.show_page("chats")
        self.show_chat_view()
        self.load_chat_history(uid)

    # ---------------------------------------
    # LOAD CHAT HISTORY
    # ---------------------------------------
    def load_chat_history(self, other_uid):
        from user_auth.firebase_config import db
        from messaging.send_message import decrypt_message, grab_symmetric_key

        self.chat_window.config(state="normal")
        self.chat_window.delete('1.0', tk.END)

        conv = db.child("user_messages").child(self.uuid).child(other_uid).get()

        if not conv or conv.val() is None:
            self.chat_window.insert(tk.END, "No messages yet.\n")
            self.chat_window.config(state="disabled")
            return

        symmetric_key = grab_symmetric_key(self.uuid)
        chat = []

        for msg_id, data in conv.val().items():
            sender = data.get("sender")
            receiver = data.get("receiver")
            encrypted = data.get("message")
            timestamp = data.get("timestamp")

            if None in (sender, receiver, encrypted, timestamp):
                continue

            chat.append(data)

        chat.sort(key=lambda x: x["timestamp"])

        for m in chat:
            sender = m["sender"]
            encrypted = m["message"].encode()

            try:
                decrypted = decrypt_message(encrypted, symmetric_key)
            except:
                decrypted = "[Decryption Failed]"

            sender_name = "You" if sender == self.uuid else "Friend"
            self.chat_window.insert(tk.END, f"{sender_name}: {decrypted} 🔒\n")

        self.chat_window.config(state="disabled")

    # ---------------------------------------
    # MESSAGE LISTENER THREAD
    # ---------------------------------------
    def start_listener(self):
        thread = threading.Thread(target=listen_for_messages, args=(self.uuid, self.display_incoming_message))
        thread.daemon = True
        thread.start()

    def display_incoming_message(self, msg):
        if msg["sender"] == self.active_receiver:
            self.display_message(f"{msg['sender']}: {msg['message']} 🔒")
        self.load_conversation_previews()

    # ---------------------------------------
    # UI REFRESH LOOP (POLL NEW MESSAGES)
    # ---------------------------------------
    def start_chat_refresh(self):
        def refresh():
            if self.uuid:
                if self.active_receiver:
                    self.load_chat_history(self.active_receiver)
                self.load_conversation_previews()
            self.root.after(1500, refresh)

        refresh()

    # ---------------------------------------
    # PAGE: CHATS
    # ---------------------------------------
    def create_chats_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.pages["chats"] = frame
        self.apply_gradient(frame)

        # Chats list (conversation previews)
        self.chats_list_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ctk.CTkLabel(
            self.chats_list_frame,
            text="Chats",
            font=self.fonts["title"],
            text_color=self.ui["text"],
            fg_color="transparent",
            bg_color="transparent"
        ).pack(pady=(12, 6))

        self.chats_list = ctk.CTkScrollableFrame(
            self.chats_list_frame,
            fg_color="transparent",
            scrollbar_button_color=self.ui["card"],
            scrollbar_button_hover_color=self.ui["surface"]
        )
        self.chats_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Chat view (active conversation)
        self.chat_view_frame = ctk.CTkFrame(frame, fg_color="transparent")

        self.chat_header = ctk.CTkFrame(
            self.chat_view_frame,
            fg_color=self.ui["card"],
            corner_radius=14
        )
        self.chat_header.pack(padx=12, pady=(10, 6), fill=tk.X)

        back_btn = ctk.CTkButton(
            self.chat_header,
            text="Back",
            command=self.show_chat_list,
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=30,
            width=70
        )
        back_btn.pack(padx=10, pady=10, side=tk.LEFT)

        self.chat_title_label = ctk.CTkLabel(
            self.chat_header,
            text="Select a chat",
            font=self.fonts["heading"],
            text_color=self.ui["text"],
            fg_color="transparent",
            bg_color="transparent"
        )
        self.chat_title_label.pack(padx=8, pady=8, side=tk.LEFT)

        self.chat_window = ctk.CTkTextbox(
            self.chat_view_frame,
            wrap="word",
            fg_color=self.ui["surface"],
            text_color=self.ui["text"],
            border_color=self.ui["divider"]
        )
        self.chat_window.configure(state="disabled")
        self.chat_window.pack(padx=10, pady=(6, 10), fill=tk.BOTH, expand=True)

        self.spam_label = ctk.CTkLabel(
            self.chat_view_frame,
            text="Spam Probability: N/A",
            font=self.fonts["small"],
            text_color=self.ui["muted"],
            fg_color="transparent",
            bg_color="transparent"
        )
        self.spam_label.pack(pady=4)

        self.entry = ctk.CTkEntry(
            self.chat_view_frame,
            font=self.fonts["body"],
            fg_color=self.ui["surface"],
            text_color=self.ui["text"],
            border_color=self.ui["divider"]
        )
        self.entry.pack(padx=10, pady=6, fill=tk.X)
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(
            self.chat_view_frame,
            text="Send",
            command=self.send_message,
            fg_color=self.ui["accent"],
            hover_color=self.ui["accent_hover"],
            text_color="#041014",
            height=36
        )
        self.send_button.pack(pady=(4, 12))

    # ---------------------------------------
    # PAGE: CONTACTS
    # ---------------------------------------
    def create_contacts_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.pages["contacts"] = frame
        self.apply_gradient(frame)

        ctk.CTkLabel(
            frame,
            text="Select a contact",
            font=self.fonts["heading"],
            text_color=self.ui["text"],
            fg_color="transparent",
            bg_color="transparent"
        ).pack(pady=(12, 6))

        self.contacts_list = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
            scrollbar_button_color=self.ui["card"],
            scrollbar_button_hover_color=self.ui["surface"]
        )
        self.contacts_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.load_contacts()

    def load_contacts(self):
        from user_auth.firebase_config import db

        for widget in self.contacts_list.winfo_children():
            widget.destroy()

        users = db.child("users").get()
        self.user_map = {}

        if not users or users.val() is None:
            ctk.CTkLabel(
                self.contacts_list,
                text="No contacts found.",
                text_color=self.ui["muted"],
                fg_color="transparent",
                bg_color="transparent"
            ).pack(pady=20)
            return

        for user in users.each():
            data = user.val()
            uid = user.key()
            if uid == self.uuid:
                continue

            name = data.get("display_name", data.get("email", "Unknown User"))
            self.user_map[uid] = name
            card = ctk.CTkFrame(self.contacts_list, fg_color=self.ui["card"], corner_radius=12)
            card.pack(fill=tk.X, padx=6, pady=6)

            ctk.CTkLabel(
                card,
                text=name,
                font=self.fonts["body"],
                text_color=self.ui["text"],
                anchor="w",
                fg_color="transparent",
                bg_color="transparent"
            ).pack(fill=tk.X, padx=12, pady=(8, 2))

            ctk.CTkButton(
                card,
                text="Message",
                command=lambda u=uid: self.open_conversation(u),
                fg_color=self.ui["surface"],
                hover_color=self.ui["divider"],
                text_color=self.ui["text"],
                height=28
            ).pack(padx=12, pady=(0, 10), anchor="e")

    # ---------------------------------------
    # PAGE: PROFILE
    # ---------------------------------------
    def create_profile_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.pages["profile"] = frame
        self.apply_gradient(frame)

        ctk.CTkLabel(
            frame,
            text="Profile",
            font=self.fonts["title"],
            text_color=self.ui["text"],
            fg_color="transparent",
            bg_color="transparent"
        ).pack(pady=(16, 6))

        self.profile_image_label = ctk.CTkLabel(
            frame,
            text="",
            fg_color="transparent",
            bg_color="transparent"
        )
        self.profile_image_label.pack(pady=(8, 6))

        self.change_pic_btn = ctk.CTkButton(
            frame,
            text="Change Picture",
            command=self.choose_profile_picture,
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=30
        )
        self.change_pic_btn.pack(pady=(0, 12))

        self.profile_name_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Display name",
            fg_color=self.ui["surface"],
            text_color=self.ui["text"],
            border_color=self.ui["divider"]
        )
        self.profile_name_entry.pack(padx=18, pady=6, fill=tk.X)

        self.profile_status_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Status (e.g. Busy, Available)",
            fg_color=self.ui["surface"],
            text_color=self.ui["text"],
            border_color=self.ui["divider"]
        )
        self.profile_status_entry.pack(padx=18, pady=6, fill=tk.X)

        self.profile_save_btn = ctk.CTkButton(
            frame,
            text="Save Profile",
            command=self.save_profile,
            fg_color=self.ui["accent"],
            hover_color=self.ui["accent_hover"],
            text_color="#041014",
            height=34
        )
        self.profile_save_btn.pack(pady=(10, 6))

        self.profile_status_label = ctk.CTkLabel(
            frame,
            text="",
            text_color=self.ui["muted"],
            fg_color="transparent",
            bg_color="transparent"
        )
        self.profile_status_label.pack(pady=(4, 10))

    # ---------------------------------------
    # PAGE: SETTINGS
    # ---------------------------------------
    def create_settings_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.pages["settings"] = frame
        self.apply_gradient(frame)

        ctk.CTkLabel(
            frame,
            text="Settings Page",
            font=self.fonts["heading"],
            text_color=self.ui["text"],
            fg_color="transparent",
            bg_color="transparent"
        ).pack(pady=(20, 8))

        logout_btn = ctk.CTkButton(
            frame,
            text="Log Out",
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="white",
            font=self.fonts["body"],
            command=self.logout,
            height=36
        )
        logout_btn.pack(pady=20, padx=12)

    # ---------------------------------------
    # LOGOUT
    # ---------------------------------------
    def logout(self):
        self.root.destroy()

    # ---------------------------------------
    # BOTTOM NAVBAR
    # ---------------------------------------
    def create_navbar(self):
        navbar = ctk.CTkFrame(self.root, fg_color=self.ui["surface"], height=54)
        navbar.pack(side=tk.BOTTOM, fill=tk.X)

        ctk.CTkButton(
            navbar,
            text="Chats",
            command=lambda: self.show_page("chats"),
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=36,
            width=80
        ).pack(side=tk.LEFT, expand=True, padx=2, pady=6)
        ctk.CTkButton(
            navbar,
            text="Contacts",
            command=lambda: self.show_page("contacts"),
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=36,
            width=80
        ).pack(side=tk.LEFT, expand=True, padx=2, pady=6)
        ctk.CTkButton(
            navbar,
            text="Profile",
            command=lambda: self.show_page("profile"),
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=36,
            width=80
        ).pack(side=tk.LEFT, expand=True, padx=2, pady=6)
        ctk.CTkButton(
            navbar,
            text="Settings",
            command=lambda: self.show_page("settings"),
            fg_color=self.ui["surface"],
            hover_color=self.ui["divider"],
            text_color=self.ui["text"],
            height=36,
            width=80
        ).pack(side=tk.LEFT, expand=True, padx=2, pady=6)

    # ---------------------------------------
    # CHANGE PAGE
    # ---------------------------------------
    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)
        if page_name == "chats":
            if self.active_receiver:
                self.show_chat_view()
            else:
                self.show_chat_list()
        if page_name == "profile":
            self.load_profile()

    # ---------------------------------------
    # MESSAGE LOGIC
    # ---------------------------------------
    def display_message(self, message):
        self.chat_window.config(state="normal")
        self.chat_window.insert(tk.END, message + "\n")
        self.chat_window.see(tk.END)
        self.chat_window.config(state="disabled")

    # ---------------------------------------
    # SEND MESSAGE
    # ---------------------------------------
    def send_message(self):
        message = self.entry.get().strip()
        if not message:
            return

        self.entry.delete(0, tk.END)

        spam_prob = spam_detection.get_spam_probability(message)
        self.spam_label.configure(text=f"Spam Probability: {spam_prob:.3f}")

        self.display_message(f"You: {message}  (Spam: {spam_prob:.3f})")

        start = time.time()
        if not self.active_receiver:
            self.display_message("[Error]: Select a contact first!")
            return

        send_message.send_message(self.uuid, self.active_receiver, message)
        end = time.time()

        self.display_message(f"[RucksApp]: Sent in {end - start:.3f} seconds")
        self.load_conversation_previews()

    # ---------------------------------------
    # PROFILE LOGIC
    # ---------------------------------------
    def choose_profile_picture(self):
        file_path = filedialog.askopenfilename(
            title="Choose Profile Picture",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        if not file_path:
            return
        self.profile_picture_path = file_path
        self.update_profile_image(file_path)

    def update_profile_image(self, path):
        if not path or not os.path.exists(path):
            return
        try:
            img = Image.open(path)
            self.profile_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
            self.profile_image_label.configure(image=self.profile_img, text="")
        except Exception:
            self.profile_image_label.configure(text="Image load failed")

    def load_profile(self):
        if not self.uuid:
            return
        from user_auth.firebase_config import db

        data = db.child("users").child(self.uuid).get()
        if not data or data.val() is None:
            return

        user = data.val()
        display_name = user.get("display_name", "")
        status = user.get("status", "")
        picture_path = user.get("profile_picture", "")

        self.profile_name_entry.delete(0, tk.END)
        self.profile_name_entry.insert(0, display_name)
        self.profile_status_entry.delete(0, tk.END)
        self.profile_status_entry.insert(0, status)

        self.profile_picture_path = picture_path
        if picture_path:
            self.update_profile_image(picture_path)

    def save_profile(self):
        if not self.uuid:
            return
        from user_auth.firebase_config import db

        display_name = self.profile_name_entry.get().strip()
        status = self.profile_status_entry.get().strip()
        picture_path = getattr(self, "profile_picture_path", "")

        db.child("users").child(self.uuid).update({
            "display_name": display_name,
            "status": status,
            "profile_picture": picture_path
        })

        self.profile_status_label.configure(text="Profile saved.")

    # ---------------------------------------
    # CHATS LIST (PREVIEWS)
    # ---------------------------------------
    def show_chat_list(self):
        self.active_receiver = None
        self.active_receiver_name = None
        self.chat_title_label.configure(text="Select a chat")
        self.chat_view_frame.pack_forget()
        self.chats_list_frame.pack(fill=tk.BOTH, expand=True)
        self.load_conversation_previews()

    def show_chat_view(self):
        self.chats_list_frame.pack_forget()
        self.chat_view_frame.pack(fill=tk.BOTH, expand=True)
        if self.active_receiver_name:
            self.chat_title_label.configure(text=self.active_receiver_name)

    def load_conversation_previews(self):
        from user_auth.firebase_config import db
        from messaging.send_message import decrypt_message, grab_symmetric_key

        for widget in self.chats_list.winfo_children():
            widget.destroy()

        if not self.uuid:
            ctk.CTkLabel(
                self.chats_list,
                text="No conversations yet.",
                text_color=self.ui["muted"],
                fg_color="transparent",
                bg_color="transparent"
            ).pack(pady=20)
            return

        users = db.child("users").get()
        user_map = {}
        if users and users.val():
            for user in users.each():
                data = user.val()
                user_map[user.key()] = data.get("display_name", data.get("email", "Unknown User"))
        self.user_map = user_map

        chats = db.child("user_messages").child(self.uuid).get()
        if not chats or chats.val() is None:
            ctk.CTkLabel(
                self.chats_list,
                text="No conversations yet.",
                text_color=self.ui["muted"],
                fg_color="transparent",
                bg_color="transparent"
            ).pack(pady=20)
            return

        symmetric_key = grab_symmetric_key(self.uuid)
        previews = []

        for partner_uid, thread in chats.val().items():
            if not isinstance(thread, dict):
                continue

            latest = None
            for msg_id, data in thread.items():
                ts = data.get("timestamp", 0)
                if latest is None or ts > latest.get("timestamp", 0):
                    latest = data

            if not latest:
                continue

            encrypted = latest.get("message", "")
            try:
                decrypted = decrypt_message(encrypted.encode(), symmetric_key)
            except Exception:
                decrypted = "[Decryption Failed]"

            previews.append((latest.get("timestamp", 0), partner_uid, decrypted))

        previews.sort(key=lambda x: x[0], reverse=True)

        for ts, partner_uid, last_msg in previews:
            name = user_map.get(partner_uid, "Unknown User")
            snippet = last_msg[:40] + ("..." if len(last_msg) > 40 else "")
            card = ctk.CTkFrame(
                self.chats_list,
                fg_color=self.ui["card"],
                corner_radius=12
            )
            card.pack(fill=tk.X, padx=6, pady=6)

            ctk.CTkLabel(
                card,
                text=name,
                font=self.fonts["body"],
                text_color=self.ui["text"],
                anchor="w",
                justify="left",
                fg_color="transparent",
                bg_color="transparent"
            ).pack(fill=tk.X, padx=12, pady=(8, 0))

            ctk.CTkLabel(
                card,
                text=snippet,
                font=self.fonts["small"],
                text_color=self.ui["muted"],
                anchor="w",
                justify="left",
                fg_color="transparent",
                bg_color="transparent"
            ).pack(fill=tk.X, padx=12, pady=(2, 8))

            open_btn = ctk.CTkButton(
                card,
                text="Open",
                command=lambda u=partner_uid: self.open_conversation(u),
                fg_color=self.ui["surface"],
                hover_color=self.ui["divider"],
                text_color=self.ui["text"],
                height=28
            )
            open_btn.pack(padx=12, pady=(0, 10), anchor="e")

    # ---------------------------------------
    # ACTIVE RECEIVER
    # ---------------------------------------
    def set_active_receiver(self, uid):
        self.active_receiver = uid
        if not self.user_map:
            self.refresh_user_map()
        self.active_receiver_name = self.user_map.get(uid, "Chat")
        self.chat_title_label.configure(text=self.active_receiver_name)

    def refresh_user_map(self):
        from user_auth.firebase_config import db

        users = db.child("users").get()
        user_map = {}
        if users and users.val():
            for user in users.each():
                data = user.val()
                user_map[user.key()] = data.get("display_name", data.get("email", "Unknown User"))
        self.user_map = user_map


# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("412x732")
    root.resizable(False, False)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root.title("Quantum Messaging App")
    root.configure(bg="#0b1220")

    messaging_gui = MessagingGUI(root)
    for page in messaging_gui.pages.values():
        page.pack_forget()  # hide pages until login

    def show_login():
        LoginOverlay(root, on_login_success=lambda uid: messaging_gui.init_after_login(uid))

    SplashScreen(root, on_finish=show_login)

    root.mainloop()
