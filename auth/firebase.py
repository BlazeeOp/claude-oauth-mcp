import firebase_admin
from firebase_admin import credentials, auth
import json
import os

if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_ADMIN_JSON")

    if not firebase_json:
        raise RuntimeError("FIREBASE_ADMIN_JSON environment variable not set")

    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str):
    return auth.verify_id_token(token)
