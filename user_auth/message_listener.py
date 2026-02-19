from user_auth.firebase_config import db 
import time
import messaging.key_generator as key_generator
from cryptography.fernet import Fernet

def listen_for_messages(user_uuid, callback):
    from user_auth.firebase_config import db
    import time
    import messaging.key_generator as key_generator
    from cryptography.fernet import Fernet

    # load this user’s symmetric key
    symmetric_key = key_generator.grab_symmetric_key(user_uuid)
    f = Fernet(symmetric_key)

    last_seen = 0

    while True:
        chats = db.child("user_messages").child(user_uuid).get()

        if chats and chats.val():
            for partner_uid, thread in chats.val().items():

                # skip invalid threads
                if not isinstance(thread, dict):
                    continue

                for msg_id, data in thread.items():

                    ts = data.get("timestamp", 0)
                    encrypted = data.get("message")

                    # skip malformed
                    if encrypted is None:
                        continue

                    if ts > last_seen:
                        try:
                            decrypted = f.decrypt(encrypted.encode()).decode()
                        except Exception:
                            continue # encrypted with another key or corrupted

                        callback({
                            "sender": partner_uid,
                            "message": decrypted
                        })

                        last_seen = ts

        time.sleep(1)
 # Works here for some reason?
