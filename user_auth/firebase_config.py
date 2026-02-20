import pyrebase

firebase_config = {
    "apiKey": "REDACTED",
    "authDomain": "rucksapp-d3482.firebaseapp.com",
    "databaseURL": "https://rucksapp-d3482-default-rtdb.europe-west1.firebasedatabase.app/",
    "projectId": "rucksapp-d3482",
    "storageBucket": "rucksapp-d3482.firebasestorage.app",
    "messagingSenderId": "493629039195",
    "appId": "1:493629039195:web:1b6f3b50d2029de7c2157e"
}

firebase = pyrebase.initialize_app(firebase_config)

auth = firebase.auth()
db = firebase.database() # for the realtime database
