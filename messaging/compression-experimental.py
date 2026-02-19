# Run-Length Encoding Algorithm

def the_hexanator(message): # may be redundant as the encrypted messages should be hex already
    message = message.encode("utf-8").hex()
    return message

def RLE(message): # input the compressed message - after encryption
    print(f"Your Uncompressed Message Is: {message}")
    count = 1
    for i in range (1, len(message)):
        if message[i] == message[i-1]:
            count = count + 1
        else:
            message = message + f"{input[i - 1]}{count}"
            count = 1 # resetting the count for the new character
        return message
    message = message + f"{input[-1]}{count}"
    return message

message = str(input())
RLE_message = RLE(message)
print(RLE_message)