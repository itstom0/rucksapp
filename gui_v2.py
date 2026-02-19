import tkinter as tk
from tkinter import scrolledtext
import time

import spam_detection.main as spam_detection
import messaging.send_message as send_message

import threading
from user_auth.message_listener import listen_for_messages


class MessagingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Messaging App")
        self.root.geometry("412x732")  # updated to reflect the mobile aspect ratio

        # TEMPORARY UUIDs - will be replaced when Firebase Auth is added
        self.uuid = "123456789"              # This user's UUID (sender)
        self.active_receiver = "987654321"   # Receiver UUID for testing

        # Start message listener thread
        self.start_listener()

        # Store frames (pages)
        self.pages = {}

        # Create all pages
        self.create_chats_page()
        self.create_contacts_page()
        self.create_profile_page()
        self.create_settings_page()

        # Show chats page by default
        self.show_page("chats")

        # Bottom Navigation Bar
        self.create_navbar()

    # ---------------------------------------
    # MESSAGE LISTENER THREAD
    # ---------------------------------------
    def start_listener(self):
        thread = threading.Thread(
            target=listen_for_messages,
            args=(self.uuid, self.display_incoming_message)
        )
        thread.daemon = True
        thread.start()

    def display_incoming_message(self, msg):
        self.display_message(f"Friend: {msg}")

    # ---------------------------------------
    # PAGE: CHATS
    # ---------------------------------------
    def create_chats_page(self):
        frame = tk.Frame(self.root)
        self.pages["chats"] = frame

        # Chat window
        self.chat_window = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state="disabled")
        self.chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Spam probability label
        self.spam_label = tk.Label(frame, text="Spam Probability: N/A", font=("Arial", 11))
        self.spam_label.pack(pady=5)

        # Input field
        self.entry = tk.Entry(frame, font=("Arial", 12))
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind("<Return>", lambda event: self.send_message())

        # Send button
        self.send_button = tk.Button(frame, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)

    # ---------------------------------------
    # PAGE: CONTACTS
    # ---------------------------------------
    def create_contacts_page(self):
        frame = tk.Frame(self.root)
        self.pages["contacts"] = frame

        tk.Label(frame, text="Contacts Page", font=("Arial", 16)).pack(pady=20)
        tk.Label(frame, text="(I will add the contacts page in the next development cycle)").pack()

    # ---------------------------------------
    # PAGE: PROFILE
    # ---------------------------------------
    def create_profile_page(self):
        frame = tk.Frame(self.root)
        self.pages["profile"] = frame

        tk.Label(frame, text="Profile Page", font=("Arial", 16)).pack(pady=20)
        tk.Label(frame, text="(I will add the profile page in the next development cycle)").pack()

    # ---------------------------------------
    # PAGE: SETTINGS
    # ---------------------------------------
    def create_settings_page(self):
        frame = tk.Frame(self.root)
        self.pages["settings"] = frame

        tk.Label(frame, text="Settings Page", font=("Arial", 16)).pack(pady=20)
        tk.Label(frame, text="(Encryption toggles, app settings, etc)").pack()

    # ---------------------------------------
    # BOTTOM NAVBAR
    # ---------------------------------------
    def create_navbar(self):
        navbar = tk.Frame(self.root, bg="#e0e0e0", height=50)
        navbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Four buttons (tabs)
        tk.Button(navbar, text="Chats", command=lambda: self.show_page("chats"), width=12).pack(side=tk.LEFT, expand=True)
        tk.Button(navbar, text="Contacts", command=lambda: self.show_page("contacts"), width=12).pack(side=tk.LEFT, expand=True)
        tk.Button(navbar, text="Profile", command=lambda: self.show_page("profile"), width=12).pack(side=tk.LEFT, expand=True)
        tk.Button(navbar, text="Settings", command=lambda: self.show_page("settings"), width=12).pack(side=tk.LEFT, expand=True)

    # ---------------------------------------
    # CHANGE PAGE
    # ---------------------------------------
    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)

    # ---------------------------------------
    # MESSAGE LOGIC
    # ---------------------------------------
    def display_message(self, message):
        self.chat_window.config(state="normal")
        self.chat_window.insert(tk.END, message + "\n")
        self.chat_window.see(tk.END)
        self.chat_window.config(state="disabled")

    def send_message(self):
        message = self.entry.get().strip()
        if not message:
            return

        self.entry.delete(0, tk.END)

        # Spam detection
        spam_prob = spam_detection.get_spam_probability(message)
        self.spam_label.config(text=f"Spam Probability: {spam_prob:.3f}")

        # Display locally
        self.display_message(f"You: {message}  (Spam: {spam_prob:.3f})")

        # Send message (NOW FIXED including sender & receiver)
        start = time.time()
        send_message.send_message(self.uuid, self.active_receiver, message)
        end = time.time()

        self.display_message(f"[RucksApp] Sent in {end - start:.3f} seconds")


# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = MessagingGUI(root)
    root.mainloop()


