import bcrypt
import logging

logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using bcrypt.
    
    Bcrypt has a 72-character limit for passwords. Newer versions of the bcrypt
    library raise a ValueError if this limit is exceeded. We truncate the 
    password to 72 bytes to remain compatible and avoid crashes.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        if isinstance(plain_password, str):
            password_bytes = plain_password.encode('utf-8')
        else:
            password_bytes = plain_password
            
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Bcrypt has a 72-character limit for passwords. Newer versions of the bcrypt
    library raise a ValueError if this limit is exceeded. We truncate the 
    password to 72 bytes to remain compatible and avoid crashes.
    """
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
