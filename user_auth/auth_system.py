from user_auth.firebase_config import db, auth


def register(email, password, first_name="", surname=""):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        uid = user["localId"]
        first_name = (first_name or "").strip()
        surname = (surname or "").strip()
        display_name = f"{first_name} {surname}".strip() or email.split("@")[0]
        profile_initial = (first_name[:1] or email[:1] or "?").upper()

        # Store user info in Firebase
        db.child("users").child(uid).set({
            "email": email,
            "email_lower": email.lower(),
            "first_name": first_name,
            "surname": surname,
            "display_name": display_name,
            "profile_initial": profile_initial,
            "profile_picture": "",
            "status": ""
        })

        return uid
    except Exception as e:
        print("Registration error:", e)
        return None



def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        print("Logged in successfully.")
        uid = user["localId"]
        id_token = user["idToken"]
        return uid, id_token
    except Exception as e:
        print("Login error:", e)
        return None, None
