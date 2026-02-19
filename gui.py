# External imports
import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext
import time
import threading

# Internal imports
import spam_detection.main as spam_detection
import messaging.send_message as send_message
from user_auth.message_listener import listen_for_messages

class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.frame, text="RucksApp Login", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.frame, text="Email:").pack()
        self.email_entry = tk.Entry(self.frame)
        self.email_entry.pack(pady=5)

        tk.Label(self.frame, text="Password:").pack()
        self.password_entry = tk.Entry(self.frame, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.frame, text="Login", command=self.login).pack(pady=10)
        tk.Button(self.frame, text="Register", command=self.register).pack(pady=10)

        self.status_label = tk.Label(self.frame, text="", fg="red")
        self.status_label.pack(pady=5)

    def login(self):
        from user_auth.auth_system import login as auth_login

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        uid, token = auth_login(email, password)
        if uid:
            self.status_label.config(text="Login successful!", fg="green")
            self.frame.destroy()
            self.on_login_success(uid, self.root)
        else:
            self.status_label.config(text="Invalid login. Try again.", fg="red")

    def register(self):
        from user_auth.auth_system import register as auth_register

        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        uid = auth_register(email, password)
        if uid:
            self.status_label.config(text="Account created! Now log in.", fg="green")
        else:
            self.status_label.config(text="Registration failed.", fg="red")


class MessagingGUI:
    def __init__(self, root, uid):
        self.root = root
        self.uuid = uid # real user ID (from Firebase)
        self.active_receiver = None # Will be set when user selects a contact

        ctk.set_appearance_mode("dark") # Added later to improve the aestetics with custom-tkinter
        ctk.set_default_color_theme("blue")
        self.root.title("Quantum Messaging App")
        self.root.geometry("412x732")  # updated to reflect the mobile aspect ratio
        self.root.resizable(False, False) # I added this to lock the aspect ratio in a mobile size


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
    # OPEN CONVERSATION
    # ---------------------------------------

    def open_conversation(self, uid):
        self.active_receiver = uid
        self.show_page("chats")
        self.load_chat_history(uid)

    def load_chat_history(self, other_uid):
        from user_auth.firebase_config import db
        from messaging.send_message import decrypt_message, grab_symmetric_key

        # Clear chat window
        self.chat_window.config(state="normal")
        self.chat_window.delete('1.0', tk.END)

        # Load conversation thread from mirrored user_messages
        conv = db.child("user_messages").child(self.uuid).child(other_uid).get()

        if not conv or conv.val() is None:
            self.chat_window.insert(tk.END, "No messages yet.\n")
            self.chat_window.config(state="disabled")
            return

        # Load symmetric key for this conversation
        symmetric_key = grab_symmetric_key(self.uuid)

        chat = []

        for msg_id, data in conv.val().items():
            sender = data.get("sender")
            receiver = data.get("receiver")
            encrypted = data.get("message")
            timestamp = data.get("timestamp")

            if None in (sender, receiver, encrypted, timestamp):
                continue  # skip malformed records

            # Add to list
            chat.append(data)

        # Sort by timestamp
        chat.sort(key=lambda x: x["timestamp"])

        # Display messages decrypted
        for m in chat:
            sender = m["sender"]
            encrypted = m["message"].encode()  # convert back to bytes

            try:
                decrypted = decrypt_message(encrypted, symmetric_key)
            except:
                decrypted = "[Decryption Failed]"

            sender_name = "You" if sender == self.uuid else "Friend"

            # adding a lock icon to show the message was decrypted from encrypted DB
            self.chat_window.insert(tk.END, f"{sender_name}: {decrypted} 🔒\n")

        self.chat_window.config(state="disabled")



    # ---------------------------------------
    # LOAD CHAT HISTORY
    # ---------------------------------------

    def load_chat_history(self, other_uid):
        from user_auth.firebase_config import db
        from messaging.send_message import decrypt_message, grab_symmetric_key
    
        # Allow writing
        self.chat_window.config(state="normal")
        self.chat_window.delete('1.0', tk.END)

        # Load encrypted convo thread
        conv = db.child("user_messages").child(self.uuid).child(other_uid).get()

        if not conv or conv.val() is None:
            self.chat_window.insert(tk.END, "No messages yet.\n")
            self.chat_window.config(state="disabled")
            return

        # Get correct symmetric key
        symmetric_key = grab_symmetric_key(self.uuid)

        chat = []

        # Convert Firebase dict into a list
        for msg_id, data in conv.val().items():
            sender = data.get("sender")
            receiver = data.get("receiver")
            encrypted = data.get("message")
            timestamp = data.get("timestamp")

            if None in (sender, receiver, encrypted, timestamp):
                continue

            chat.append(data)

        # Sort chronologically
        chat.sort(key=lambda x: x["timestamp"])

        # Display messages
        for m in chat:
            sender = m["sender"]
            encrypted = m["message"].encode()

            # Decrypt safely
            try:
                decrypted = decrypt_message(encrypted, symmetric_key)
            except:
                decrypted = "[Could not decrypt]"

            sender_name = "You" if sender == self.uuid else "Friend"
            self.chat_window.insert(tk.END, f"{sender_name}: {decrypted} 🔒\n")

        self.chat_window.config(state="disabled")



    # ---------------------------------------
    # MESSAGE LISTENER THREAD
    # ---------------------------------------
    def start_listener(self):
        thread = threading.Thread(target=listen_for_messages, args=(self.uuid, self.display_incoming_message))
        target=listen_for_messages,
        args=(self.uuid, self.display_incoming_message)
    
        thread.daemon = True
        thread.start()

    def display_incoming_message(self, msg):
        # Only show messages for active chat
        if msg["sender"] == self.active_receiver:
            self.display_message(f"{msg['sender']}: {msg['message']} 🔒")


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

        tk.Label(frame, text="Select a contact", font=("Arial", 16)).pack(pady=10)

        self.contacts_list = tk.Frame(frame)
        self.contacts_list.pack(fill=tk.BOTH, expand=True)

        self.load_contacts()

    def load_contacts(self):
        from user_auth.firebase_config import db

        # Clear frame
        for widget in self.contacts_list.winfo_children():
            widget.destroy()

        users = db.child("users").get()

        # No users yet
        if not users or users.val() is None:
            tk.Label(self.contacts_list, text="No contacts found.", fg="gray").pack(pady=20)
            return

        for user in users.each():
            data = user.val()
            uid = user.key()

            # Don't show yourself
            if uid == self.uuid:
                continue

            btn = tk.Button(
                self.contacts_list,
                text=data.get("display_name", data.get("email", "Unknown User")),
                command=lambda u=uid: self.open_conversation(u),   # restores contact selection
                height=2
            )
            btn.pack(fill=tk.X, padx=10, pady=5)




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

        # Logout button
        logout_btn = tk.Button(
            frame,
            text="Log Out",
            bg="#ff3b30",
            fg="white",
            font=("Arial", 12, "bold"),
            command=self.logout
        )
        logout_btn.pack(pady=20, ipadx=10, ipady=5)
    
    def logout(self):
        # Close the current Messaging GUI window
        self.root.destroy()

        # Relaunch login window
        restart_login()


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

    # ---------------------------------------
    # EXAMPLE PHONE TOP-BAR
    # ---------------------------------------
    def create_topbar(self):
        self.topbar = ctk.CTkFrame(
            self.root,
            height=32,
            fg_color="#020617"
        )
        self.topbar.pack(fill=tk.X)

        status = ctk.CTkLabel(
            self.topbar,
            text="12:47   📶  🔋",
            text_color="white",
            font=("Arial", 12)
        )
        status.pack(side=tk.RIGHT, padx=10)

    # ---------------------------------------
    # LOGOUT BUTTON FUNCTION
    # ---------------------------------------
    def logout(self):
        # Destroy the current window (main app)
        self.root.destroy()

        restart_login()  # call your login launcher

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

        # Send message (NOW FIXED includes sender & receiver)
        start = time.time()
        if not self.active_receiver: # No contact selected
            self.display_message("[Error]: Select a contact first!")
            return

        send_message.send_message(self.uuid, self.active_receiver, message) # This is the call of my send_message() function
        # problem I was encountering was due to the incorrect order of parameters
        #Solution: I changed the order of parameters to match the function definition

        # send_message.send_message(self.uuid, self.active_receiver, message) redundant
        end = time.time()

        self.display_message(f"[RucksApp]: Sent in {end - start:.3f} seconds") # incoporated timing stats into this instead of the old messaging module


def restart_login():
    root = tk.Tk()
    LoginWindow(root, start_main_app)
    login_root.mainloop()

def start_main_app(uid, login_root):
    login_root.destroy() # Close the login window
    new_root = tk.Tk() # Create a new window for the messaging app
    MessagingGUI(new_root, uid)
    new_root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root, start_main_app)
    root.mainloop()