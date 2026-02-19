import time
import secrets
from pathlib import Path

import qsharp

from user_auth.firebase_config import db

key_store = []
key_counter = 0

class qubit:
    def __init__(self, count, state, prob):
        self.count = count
        self.state = state
        self.prob = prob


_QSHARP_RANDOM_BIT_DEFINED = False
_QSHARP_RANDOM_BIT_OP = "Messaging.RandomBit()"


def _qsharp_random_bit():
    global _QSHARP_RANDOM_BIT_DEFINED

    if not _QSHARP_RANDOM_BIT_DEFINED:
        qs_path = Path(__file__).with_name("bit_generator.qs")
        qsharp.compile(qs_path.read_text())
        _QSHARP_RANDOM_BIT_DEFINED = True

    result = qsharp.eval(_QSHARP_RANDOM_BIT_OP)
    return 1 if str(result).lower() in {"one", "1", "true"} else 0

def startup(key_count): # Key count is pointless here, but kept incase it breaks things removing.
    print("Welecome to:\n")
    print("████████╗ ██████╗ ███╗   ███╗███████╗     ██████╗ ██╗  ██╗ ██████╗ ")
    print("╚══██╔══╝██╔═══██╗████╗ ████║██╔════╝    ██╔═══██╗██║ ██╔╝██╔════╝")
    print("   ██║   ██║   ██║██╔████╔██║███████╗    ██║   ██║█████╔╝ ██║  ███╗")
    print("   ██║   ██║   ██║██║╚██╔╝██║╚════██║    ██║▄▄ ██║██╔═██╗ ██║   ██║")
    print("   ██║   ╚██████╔╝██║ ╚═╝ ██║███████║    ╚██████╔╝██║  ██╗╚██████╔╝")
    print("   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚══════╝     ╚══▀▀═╝ ╚═╝  ╚═╝ ╚═════╝ ")
    print("- Part of RucksApp\n")

def collapse_qubit():
    return qubit(1, _qsharp_random_bit(), 0.5).state # this was from when I used python to simulate the Q# function, it "collapses a qubit into either a 1 or 0"

def key_generate():
    rucks_master_key = ""
    rucks_giga_key = ""
    while len(rucks_giga_key) < 43:  # 64 hex digits = 256 bits
        rucks_master_key += str(collapse_qubit())
        if len(rucks_master_key) == 4:
            rucks_giga_key += hex(int(rucks_master_key, 2))[2:]
            rucks_master_key = ""
    if len(rucks_giga_key) == 43: # This is a simple validation, to ensure the key is 64 hex digits long, else we re-generate.
        return rucks_giga_key # This should be mostly redundant, but is a safety check.
    else:
        key_generate() # It must be 64 hex digits, to seperate back into the key, UUID and nonce later.

def grab_key():
    key = key_generate()
    return key

def wait_Time(tempus): # required as time.sleep did not work :(
    ut = time.time()
    while time.time() - ut < tempus:
        x=1

def grab_symmetric_key(UUID):
    nonce = secrets.token_urlsafe()

    # Reuse a stored key if it exists, otherwise generate and store one.
    stored = db.child("user_keys").child(UUID).get()
    if stored and stored.val():
        symmetric_key = stored.val()
    else:
        key_location = key_generation(key_counter)
        master_key = key_store[key_location - 1]
        symmetric_key = master_key
        # symmetric_key = nonce + master_key + UUID - no key derrivation function yet
        while len(symmetric_key) < 44:
            if len(symmetric_key) == 43:
                symmetric_key = symmetric_key + "="  # Fernet keys must be 44 bytes, so we add padding.
            else:
                symmetric_key = symmetric_key[:-1]
        db.child("user_keys").child(UUID).set(symmetric_key)

    return symmetric_key

def local_store_keys(current_key):
    key_store.append(current_key)


def key_generation(key_counter):
    current_key = grab_key()
    local_store_keys(current_key)
    key_counter = key_counter + 1
    return key_counter

    
startup(key_counter)
