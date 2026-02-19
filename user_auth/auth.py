from user_auth.firebase_config import auth

def register(email, password):
    user = auth.create_user_with_email_and_password(email, password)
    return user['localId']  # Firebase UID

def login(email, password):
    user = auth.sign_in_with_email_and_password(email, password)
    return user['localId'], user['idToken']
