# External packages
import tkinter as tk
from tkinter import scrolledtext
import time

# Internal modules
import spam_detection.main as spam_detection
import messaging.send_message as send_message

class MessagingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Messaging App - Test GUI") # Set the window title
        self.root.geometry("500x600") # Set the window size

        # ---- Message Display Window ----
        self.chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, state="disabled")
        self.chat_window.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # ---- Spam Probability Label ----
        self.spam_label = tk.Label(root, text="Spam Probability: N/A", font=("Arial", 11))
        self.spam_label.pack(pady=5)

        # ---- Input Field ----
        self.entry = tk.Entry(root, font=("Arial", 12))
        self.entry.pack(padx=10, pady=5, fill=tk.X)
        self.entry.bind("<Return>", lambda event: self.send_message())

        # ---- Send Button ----
        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack(pady=10)

    def display_message(self, message): # Displays message in the chat window
        self.chat_window.config(state="normal")
        self.chat_window.insert(tk.END, message + "\n")
        self.chat_window.see(tk.END)
        self.chat_window.config(state="disabled")

    def send_message(self): # Handles message input, spam detection, sending, and output display.
        message = self.entry.get().strip()
        if not message:
            return

        # Clears the entry box
        self.entry.delete(0, tk.END)

        # 1. Get spam probability
        spam_prob = spam_detection.get_spam_probability(message)
        self.spam_label.config(text=f"Spam Probability: {spam_prob:.3f}")

        # Add to the local chat feed
        self.display_message(f"You: {message}  (Spam: {spam_prob:.3f})")

        # 2. Send message through the backend
        start = time.time()
        send_message.send_message(message)
        end = time.time()

        # Show time taken (just a more streamlined version of my ut-ft calc)
        self.display_message(f"[RucksApp] Message sent in {end - start:.3f} seconds")

root = tk.Tk()
gui = MessagingGUI(root)
root.mainloop()
