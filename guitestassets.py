from customtkinter import *
from PIL import Image

app = CTk()
app.geometry("412x732") # initiales the app container which is size appropriate for a phone.

set_appearance_mode("dark") # this will allow me to create a toggleable light / dark mode

chat_icon_dark = Image.open("assets/chat_icon_dark.png") # dark mode chat icon
chat_icon_light = Image.open("assets/chat_icon_light.png")# light mode chat icon

btn = CTkButton(master=app, text="Chat Now...", corner_radius=32,
                fg_color="transparent", hover_color="#4158D0", border_color="#FFCC70", border_width=2, # the corner radius allows for rounded buttons, which is better to fufil stakeholder expectations
                image = CTkImage(dark_image=chat_icon_dark, light_image=chat_icon_light)) # here I am defining both a light and dark mode version of the icon

btn.place(relx=0.5, rely=0.5, anchor="center") # creating the button and anchoring it to the middle

app.mainloop()

