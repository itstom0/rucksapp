import messaging.send_message as send_message
import spam_detection.main as spam_detection
import time

def spam_detection_check(message):
    spam_prob = spam_detection.get_spam_probability(message) # Get spam probability of the message
    print(f"Spam probability: {spam_prob:.4f}")
    if spam_prob > 0.8:
        print("Warning: The message is likely spam. Please modify the content before sending.")
        return 1 # This indicates to the program to not send the message
    else:
        return 0 # This indicates to the program to proceed with sending the message

while True:
    message = str(input("Enter the message to send: ")) # Allows user to input a message
    check = spam_detection_check(message) # Performs spam detection check on message
    if check == 0:
        ut = time.time()
        send_message.send_message(message) # This will no longer work independantly as we need sender and receiver UUIDs now
        ft = time.time()
        print(f"Total time taken for the entire process: {ft - ut} seconds.")
    else:
        print("Message sending aborted due to high spam probability.")