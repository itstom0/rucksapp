# External imports
import time
from cryptography.fernet import Fernet

# Internal imports
from user_auth.firebase_config import db
import messaging.key_generator as key_generator

UUID = "123456789"  # This accounts placeholder UUID - pretty much redundant for the current implementation.

def grab_symmetric_key(UUID):
    symmetric_key = key_generator.grab_symmetric_key(UUID)
    print(symmetric_key)
    return symmetric_key

def encrypt_message(plaintext, symmetric_key):
    fernet = Fernet(symmetric_key)
    encMessage = fernet.encrypt(plaintext.encode())
    print("original string: ", plaintext)
    print("encrypted string: ", encMessage)
    return encMessage

def decrypt_message(encMessage, symmetric_key):
    fernet = Fernet(symmetric_key)
    decMessage = fernet.decrypt(encMessage).decode()
    return decMessage

def upload_encrypted_message(sender_uuid, receiver_uuid, encrypted_bytes):
    message_data = {
        "sender": sender_uuid,
        "receiver": receiver_uuid,
        "timestamp": time.time(),
        "message": encrypted_bytes.decode()
    }
    # 1. The global message log (not strictly necessary, but useful debugging)
    db.child("messages").push(message_data)
    # 2. The sender's conversation thread
    db.child("user_messages").child(sender_uuid).child(receiver_uuid).push(message_data)
    # 3. The receiver's conversation thread
    db.child("user_messages").child(receiver_uuid).child(sender_uuid).push(message_data)



def send_message(sender_uuid,  receiver_uuid, message): # Remeber new parameter receiver_uuid
    ut = time.time()
    symmetric_key = grab_symmetric_key(sender_uuid) # Migrating the code from UUID to the new sender_uuid
    encrypted_message = encrypt_message(message, symmetric_key)
    upload_encrypted_message(sender_uuid, receiver_uuid, encrypted_message)

     #Testing decryption time (here for demonstration purposes)
    decrypted_message = decrypt_message(encrypted_message, symmetric_key)
    print("decrypted string: ", decrypted_message)
    ft = time.time()
    print("Time taken to encrypt and decrypt the message: ", ft - ut)
    print("\n")
    
    return encrypted_message