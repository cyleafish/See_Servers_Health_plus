import os
from dotenv import load_dotenv

load_dotenv()
ALLOWED_IDS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip().isdigit()]

def is_user_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_IDS
