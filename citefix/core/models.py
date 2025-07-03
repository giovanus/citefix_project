from mongoengine import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
from mongoengine.queryset.visitor import Q
import requests
import os
from .config import *


# === UTILISATEUR ===
class Utilisateur(Document):
    ROLES = ('CITOYEN', 'AUTORITE', 'TECHNICIEN', 'ADMIN', 'SYS')
    ROLE_INDEX = {role: i+1 for i, role in enumerate(ROLES)}
    email = EmailField(required=True, unique=True)
    telephone = StringField(required=True, unique=True)
    mot_de_passe = StringField(required=True)  # À hasher avec bcrypt ou passlib côté service
    nom = StringField()
    prenom = StringField()
    photo_profil = StringField()  # URL ou nom de fichier
    bio = StringField()
    date_naissance = DateField()
    role = StringField(choices=ROLES, required=True, default=ROLES[0])
    est_actif = BooleanField(default=False)
    date_inscription = DateTimeField(default=datetime.now)
    
    def date_inscription_since(self):
        now = datetime.now()
        delta = relativedelta(now, self.date_inscription)

        if delta.years > 0:
            return f"Inscrit(e) depuis {delta.years} an{'s' if delta.years > 1 else ''}"
        elif delta.months > 0:
            return f"Inscrit(e) depuis {delta.months} mois"
        elif delta.days > 0:
            return f"Inscrit(e) depuis {delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.hours > 0:
            return f"Inscrit(e) depuis {delta.hours} heure{'s' if delta.hours > 1 else ''}"
        elif delta.minutes > 0:
            return f"Inscrit(e) depuis {delta.minutes} minute{'s' if delta.minutes > 1 else ''}"
        else:
            return "Inscrit(e) à l'instant"
    
    def role_css_class(self):
        return f"role-{Utilisateur.ROLE_INDEX[self.role]}"
    
    def initiales(self):
        return f"{self.nom[0]}{self.prenom[0]}".upper()
    
    def is_citoyen(self):
        return self.role == "CITOYEN"
    
    def is_autorite(self):
        return self.role == "AUTORITE"
    
    def is_technicien(self):
        return self.role == "TECHNICIEN"
    
    def is_admin(self):
        return self.role == "ADMIN"
    
    def is_sys(self):
        return self.role == "SYS"

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.role})"
    
    def date_naissance_str(self):
        date_str = self.date_naissance.strftime("%Y-%m-%d") if self.date_naissance else ""
        if date_str != "":
            return date_str
        return "Non définie"
    
    def date_naissance_str2(self):
        date_str = self.date_naissance.strftime("%d-%m-%Y") if self.date_naissance else ""
        if date_str != "":
            return date_str
        return "Non définie"
    
    def date_naissance_str3(self):
        if self.date_naissance:
            return self.date_naissance
        return "Non renseignée"

    def plaintes(self):
        return Plainte.objects(auteur=self)

    def plaintes_rev(self):
        return self.plaintes().order_by("-date_creation")

    def nom_prenom(self):
        return f"{self.nom} {self.prenom}"

    def prenom_nom(self):
        return f"{self.prenom} {self.nom}"
    
    def has_no_plaintes(self):
        return self.plaintes().count() == 0
    
    def nb_plaintes(self):
        return f"{self.plaintes().count()}".zfill(2)
    
    def last_platform_plaintes():
        return Plainte.objects().order_by("-date_creation")[:NB_PLAINTE_A_AFFICHER]
    
    def conversations(self):
        return Conversation.objects(Q(user1=self) | Q(user2=self)).order_by('-date_modification')

    def has_no_conversations(self):
        return self.conversations().count() == 0
    

# === CATEGORIE DE PLAINTE ===
class Categorie(Document):
    nom = StringField(required=True, unique=True)
    description = StringField()

    def __str__(self):
        return self.nom

# === LIEU ===
class Lieu(Document):
    longitude = FloatField(required=True)
    latitude = FloatField(required=True)

    def __str__(self):
        return f'({self.latitude}, {self.longitude})'

    def get_location_name(self):
        try:
            api_key = "15d3d7b552fb4328be6ad58265456902"

            url = "https://api.opencagedata.com/geocode/v1/json"
            params = {
                "key": api_key,
                "q": f"{self.latitude},{self.longitude}",
                "language": "fr",
                "pretty": 1,
                "no_annotations": 1
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['results']:
                components = data['results'][0]['components']
                quartier = components.get('suburb') or components.get('neighbourhood') or components.get('village')
                ville = components.get('city') or components.get('town') or components.get('municipality')

                if quartier and ville:
                    return f"{quartier}, {ville}"
                elif ville:
                    return ville
                else:
                    return data['results'][0]['formatted']

            return "Localisation inconnue"
        except Exception as e:
            return f"Erreur : {str(e)}"

# === MEDIA ===
class Media(Document):
    TYPES = ('image', 'video')

    url = StringField(required=True)
    type = StringField(choices=TYPES, required=True)
    plainte = ReferenceField('Plainte', required=True)
    date_ajout = DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.type.upper()} - {self.url}"
    
    def is_video(self):
        if ".mp4" in self.url or ".avi" in self.url or ".mov" in self.url or ".mkv" in self.url:
            return True
        return False

# === PLAINTE ===
class Plainte(Document):
    STATUTS = (
        'Signalée', 'Validée', 'Rejetée', 'Affectée',
        'En intervention', 'Fin d’intervention', 'Réglée',
        'Résolue', 'Non résolue'
    )
    
    STATUT_INDEX = {statut: i+1 for i, statut in enumerate(STATUTS)}

    auteur = ReferenceField(Utilisateur, required=True)
    description = StringField(required=True)
    titre = StringField(required=True)
    categorie = ReferenceField(Categorie, required=False, default=None)
    statut = StringField(choices=STATUTS, default='Signalée')
    localisation = ReferenceField(Lieu, required=False, default=None)
    date_creation = DateTimeField(default=datetime.now)
    technicien = ReferenceField(Utilisateur, required=False, default=None)
    autorite = ReferenceField(Utilisateur, required=False, default=None)
    
    
    def can_be_affect_to(self):
        return self.statut in [Plainte.STATUTS[1], Plainte.STATUTS[3], Plainte.STATUTS[6]]
    
    def cant_be_touched(self):
        return self.statut in [Plainte.STATUTS[7], Plainte.STATUTS[8], Plainte.STATUTS[2]]
    
    def is_just_affect(self):
        return self.statut in [Plainte.STATUTS[3], Plainte.STATUTS[1]]
    
    def is_on_intervention(self):
        return self.statut == Plainte.STATUTS[4]
    
    def is_at_intervention_end(self):
        return self.statut in [Plainte.STATUTS[5], Plainte.STATUTS[6]]
    
    def set_status_to_index(self, index):
        if index in range(len(Plainte.STATUTS)):
            self.statut = Plainte.STATUTS[index]

    def __str__(self):
        return f"Plainte #{str(self.id)[:6]} - {self.statut}"
    
    def categorie_str(self):
        if not self.categorie:
            return "Non définie"
        return self.categorie.nom

    def since(self):
        now = datetime.now()
        delta = relativedelta(now, self.date_creation)

        if delta.years > 0:
            return f"il y a {delta.years} an{'s' if delta.years > 1 else ''}"
        elif delta.months > 0:
            return f"il y a {delta.months} mois"
        elif delta.days > 0:
            return f"il y a {delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.hours > 0:
            return f"il y a {delta.hours} heure{'s' if delta.hours > 1 else ''}"
        elif delta.minutes > 0:
            return f"il y a {delta.minutes} minute{'s' if delta.minutes > 1 else ''}"
        else:
            return "il y a quelques secondes"

    def medias(self):
        return Media.objects(plainte=self)
    
    def statut_css_class(self):
        return f"statut_plainte-{Plainte.STATUT_INDEX[self.statut]}"
    
    def commentaires(self):
        return Commentaire.objects(plainte=self).order_by("-date_creation")
    
    def nb_likes(self):
        return Reaction.objects(plainte=self, type_reaction="like").count()
    
    def nb_dislikes(self):
        return Reaction.objects(plainte=self, type_reaction="dislike").count()
    
    def nb_likes_str(self):
        return f'{self.nb_likes()}'.zfill(2)
    
    def nb_dislikes_str(self):
        return f'{self.nb_dislikes()}'.zfill(2)
    
    def nb_comments(self):
        return self.commentaires().count()
    
    def nb_comments_str(self):
        return f"{self.nb_comments()}".zfill(2)
    
    def has_no_comment(self):
        return self.nb_comments() == 0
    
    def has_no_autorite(self):
        return self.autorite == None
    
    def has_no_technicien(self):
        return self.technicien == None
    
        

def last_platform_plaintes():
    return Plainte.objects().order_by("-date_creation")[:NB_PLAINTE_A_AFFICHER]

# === COMMENTAIRE ===
class Commentaire(Document):
    plainte = ReferenceField(Plainte, required=True)
    auteur = ReferenceField(Utilisateur, required=True)
    texte = StringField(required=True)
    date_creation = DateTimeField(default=datetime.now)

    def __str__(self):
        return f"Commentaire de {self.auteur.nom} sur plainte {str(self.plainte.id)[:6]}"
    
    def since(self):
        now = datetime.now()
        delta = relativedelta(now, self.date_creation)

        if delta.years > 0:
            return f"il y a {delta.years} an{'s' if delta.years > 1 else ''}"
        elif delta.months > 0:
            return f"il y a {delta.months} mois"
        elif delta.days > 0:
            return f"il y a {delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.hours > 0:
            return f"il y a {delta.hours} heure{'s' if delta.hours > 1 else ''}"
        elif delta.minutes > 0:
            return f"il y a {delta.minutes} minute{'s' if delta.minutes > 1 else ''}"
        else:
            return "il y a quelques secondes"
        
# === REACTION ===
class Reaction(Document):
    plainte = ReferenceField(Plainte, required=True)
    utilisateur = ReferenceField(Utilisateur, required=True)
    type_reaction = StringField(choices=['like', 'dislike'], required=True)
    date = DateTimeField(default=datetime.now)

    meta = {
        'indexes': [
            {'fields': ('plainte', 'utilisateur'), 'unique': True}
        ]
    }

# === RECOMPENSE ===
class Recompense(Document):
    plainte = ReferenceField(Plainte, required=True)
    montant = FloatField(required=True)
    beneficiaire = ReferenceField(Utilisateur, required=True)
    role_benef = StringField(choices=['citoyen', 'technicien'], required=True)
    date_attribution = DateTimeField(default=datetime.now)

class Conversation(Document):
    user1 = ReferenceField(Utilisateur, required=True)
    user2 = ReferenceField(Utilisateur, required=True)
    date_modification = DateTimeField(default=datetime.now)
    
    def messages(self):
        return Message.objects(conversation=self)
    
    def rep_msg(self):
        msg = self.messages().order_by("-date_envoi").first()
        if msg:
            if len(msg.text) <= 40:
                return msg.text
            else:
                return f'{f"{msg.text}"[:40]}...'
        return "---"
    
    def rep_msg_time(self):
        msg = self.messages().order_by("-date_envoi").first()
        if msg:
            return msg.date_envoi
        return "--:--"
    
    def get_other_user(self, user):
        if self.user1 == user:
            return self.user2
        elif self.user2 == user:
            return self.user1
        else:
            return None
    
class Message(Document):
    conversation = ReferenceField(Conversation, required=True)
    sender = ReferenceField(Utilisateur, required=True)
    text = StringField(required=True)
    date_envoi = DateTimeField(default=datetime.now)
    
    def is_last_msg(self):
        return self.conversation.messages().order_by("-date_envoi").first().id == self.id
    
    def medias(self):
        return MessageMedia.objects(message=self)

class MessageMedia(Document):
    TYPES = ('image', 'video')

    url = StringField(required=True)
    type = StringField(choices=TYPES, required=True)
    message = ReferenceField(Message, required=True)
    date_ajout = DateTimeField(default=datetime.now)

    def __str__(self):
        return f"{self.type.upper()} - {self.url}"
    
    def is_video(self):
        if ".mp4" in self.url or ".avi" in self.url or ".mov" in self.url or ".mkv" in self.url:
            return True
        return False


