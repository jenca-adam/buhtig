import models
import hashlib
def sha224(t):
    return hashlib.sha224(t.encode()).hexdigest()

def verify_password(username,pw):
    print('VERIFY',username,pw)
    us=models.user_by_uname(username) 
     
    if not list(us):
        return False
    if us[0].pw==sha224(''):#not yet set pw
        return False
    return us[0].pw==sha224(pw)
