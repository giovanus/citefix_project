from core.models import *
import bcrypt

hashed_pw = bcrypt.hashpw("Lucio@7410".encode(), bcrypt.gensalt()).decode()
sys = Utilisateur(
    email="adminsys@citefix.com",
    mot_de_passe=hashed_pw,
    nom = "ADMIN",
    prenom = "Système",
    role = "SYS",
    telephone= "0166000000",
)
sys.save()

hashed_pw = bcrypt.hashpw("Lucio@7410".encode(), bcrypt.gensalt()).decode()
admin = Utilisateur(
    email="admin@citefix.com",
    mot_de_passe=hashed_pw,
    nom = "ADMIN",
    prenom = "Proprio",
    role = "ADMIN",
    telephone= "0166000001",
)
admin.save()

exit()
