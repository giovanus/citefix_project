from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
import bcrypt
from .utils import save_file

def index(request):
    plaintes = last_platform_plaintes()
    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }
    context["plaintes"] = plaintes
    user_id = request.session.get("user_id", None)
    user = None
    if user_id:
        user = Utilisateur.objects(id=user_id).first()
    context["user"] = user
    if request.POST:
        texte = request.POST.get("commentaire", None)
        plainte_id = request.POST.get("plainte_id", None)
        plainte = Plainte.objects(id=plainte_id).first()
        if not user:
            return redirect("/connexion")
        commentaire = Commentaire(
            plainte = plainte,
            auteur = user,
            texte = texte
        )
        commentaire.save()
        return redirect("/")
    return render(request, 'index.html', context)

def delete_comment(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    comment = Commentaire.objects(id=id).first()
    if comment.auteur != user:
        request.session["error"] = "Vous ne disposez pas des droits de suppression sur ce commentaire !!!"
        return redirect("/")
    comment.delete()
    request.session["success"] = "Commentaire supprimé avec succés !!!"
    return redirect("/")
    

def register_view(request):
    if request.session.get("user_id", None):
        return redirect("profil")
    
    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None),
        "roles": ('CITOYEN', 'TECHNICIEN')
    }

    if request.method == 'POST':
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)
        repassword = request.POST.get('repassword', None)
        nom = request.POST.get('nom', None)
        prenom = request.POST.get('prenom', None)
        role = request.POST.get('role', None)
        telephone = request.POST.get('telephone', None)

        if not all([email, password, repassword, nom, prenom, role, telephone]):
            request.session["error"] = "Tous les champs sont à renseigner !!!"
            return redirect('inscription')

        if password != repassword:
            request.session["error"] = "Les mots de passe ne correspondent pas !!!"
            return redirect('inscription')

        if Utilisateur.objects(email=email).first():
            request.session["error"] = "Email déjà utilisé."
            return redirect('inscription')

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        Utilisateur(
            email=email,
            mot_de_passe=hashed_pw,
            nom=nom,
            prenom=prenom,
            role=role,
            telephone=telephone
        ).save()
        request.session["success"] = "Compte créé avec succès. Connecte-toi maintenant."
        return redirect('connexion')

    return render(request, 'auth/signin.html', context)


def login_view(request):
    if request.session.get("user_id", None):
        return redirect("profil")
    
    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = Utilisateur.objects(email=email).first()

        if not password:
            request.session["error"] = "Renseignez le mot de passe !!!"
            return redirect("connexion")

        if user and bcrypt.checkpw(password.encode(), user.mot_de_passe.encode()):
            request.session['user_id'] = str(user.id)
            user.est_actif = True
            user.save()
            return redirect('profil')

        request.session["error"] = "Identifiants incorrects."
        return redirect("connexion")

    return render(request, 'auth/login.html', context)


def logout(request):
    if not request.session.get("user_id"):
        return redirect("connexion")
    user = Utilisateur.objects(id=request.session["user_id"]).first()
    user.est_actif = False
    user.save()
    request.session.flush()
    return redirect("/")


def profil(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user

    if request.method == "POST":
        if 'nom' in request.POST:
            nom = request.POST.get("nom", None)
            prenom = request.POST.get("prenom", None)
            bio = request.POST.get("bio", None)
            date_naissance = request.POST.get("date_naissance", None)
            photo = request.FILES.get("photo")

            if photo:
                user.photo_profil = save_file(photo, "profil_user")
            if nom:
                user.nom = nom.strip()
            if prenom:
                user.prenom = prenom.strip()
            if bio:
                user.bio = bio.strip()
            if date_naissance:
                user.date_naissance = date_naissance
            user.save()

            request.session['success'] = "Informations mises à jour avec succès !!!"
            return redirect("profil")

        elif 'oldPassword' in request.POST:
            oldPassword = request.POST.get('oldPassword')
            newPassword = request.POST.get('newPassword')
            rePassword = request.POST.get('rePassword')

            if not bcrypt.checkpw(oldPassword.encode(), user.mot_de_passe.encode()):
                request.session['error'] = "Mot de passe incorrect !!!"
                return redirect("profil")

            if newPassword != rePassword:
                request.session['error'] = "Les mots de passe ne correspondent pas !!!"
                return redirect("profil")

            hashed_pw = bcrypt.hashpw(newPassword.encode(), bcrypt.gensalt()).decode()
            user.mot_de_passe = hashed_pw
            user.save()

            request.session['success'] = "Mot de passe modifié avec succès !!!"
            return redirect("profil")

    return render(request, "app/profil.html", context)


def profil_utilisateur(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    utilisateur = Utilisateur.objects(id=id).first()

    context["user"] = user
    context["utilisateur"] = utilisateur
    
    if request.POST:
        texte = request.POST.get("commentaire", None)
        plainte_id = request.POST.get("plainte_id", None)
        plainte = Plainte.objects(id=plainte_id).first()
        if not user:
            return redirect("/connexion")
        commentaire = Commentaire(
            plainte = plainte,
            auteur = user,
            texte = texte.strip()
        )
        commentaire.save()
        request.session["success"] = "Plainte ajoutée avec succès !!!"
        return redirect(f"/profil_utilisateur/{utilisateur.id}")

    return render(request, "app/profil_user.html", context)


def add_plainte(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None),
        "categories": Categorie.objects()
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user

    if request.method == "POST":
        titre = request.POST.get("titre")
        description = request.POST.get("description")
        medias = request.FILES.getlist("medias")
        lat = request.POST.get('latitude')
        long = request.POST.get('longitude')

        if not all([titre, description, lat, long]):
            request.session['error'] = "Tous les champs sont obligatoires !!!"
            return redirect("add_plainte")

        lieu = Lieu(longitude=long, latitude=lat)
        lieu.save()

        plainte = Plainte(
            auteur=user,
            titre=titre.strip(),
            description=description.strip(),
            localisation=lieu
        )
        plainte.save()

        # Créer les objets Media liés
        for media_file in medias:
            filename = save_file(media_file, "plaintes")
            extension = filename.split('.')[-1].lower()
            media_type = 'video' if extension in ['mp4', 'avi', 'mov'] else 'image'

            Media(
                url=filename,
                type=media_type,
                plainte=plainte
            ).save()

        request.session['success'] = "Plainte ajoutée avec succès !!!"
        return redirect("mes_plaintes")

    return render(request, 'app/plaintes/add.html', context)


def mes_plaintes(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if request.POST:
        texte = request.POST.get("commentaire", None)
        plainte_id = request.POST.get("plainte_id", None)
        plainte = Plainte.objects(id=plainte_id).first()
        if not user:
            return redirect("/connexion")
        commentaire = Commentaire(
            plainte = plainte,
            auteur = user,
            texte = texte.strip()
        )
        commentaire.save()
        request.session["success"] = "Plainte ajoutée avec succès !!!"
        return redirect("/mes_plaintes")

    return render(request, "app/plaintes/list2.html", context)

def view_plainte(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=id).first()
    context["plainte"] = plainte
    if request.POST:
        texte = request.POST.get("commentaire", None)
        plainte_id = request.POST.get("plainte_id", None)
        plainte = Plainte.objects(id=plainte_id).first()
        if not user:
            return redirect("/connexion")
        commentaire = Commentaire(
            plainte = plainte,
            auteur = user,
            texte = texte.strip()
        )
        commentaire.save()
        request.session["success"] = "Plainte ajoutée avec succès !!!"
        return redirect(f"/mes_plaintes/{id}/view")
    return render(request, "app/plaintes/view.html", context)

def delete_plainte(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    user = Utilisateur.objects(id=request.session["user_id"]).first()

    plainte = Plainte.objects(id=id).first()
    if not plainte or plainte.auteur != user:
        request.session["error"] = "Vous n'êtes pas autorisé à supprimer cette plainte !!!"
    else:
        Media.objects(plainte=plainte).delete()  # Supprimer aussi les médias associés
        plainte.delete()
        request.session["success"] = "Plainte supprimée avec succès !!!"

    return redirect("mes_plaintes")

def delete_comment2(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    comment = Commentaire.objects(id=id).first()
    if comment.auteur != user:
        request.session["error"] = "Vous ne disposez pas des droits de suppression sur ce commentaire !!!"
        return redirect("/mes_plaintes")
    comment.delete()
    request.session["success"] = "Commentaire supprimé avec succés !!!"
    return redirect("/mes_plaintes")

def delete_comment3(request,id, from_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    comment = Commentaire.objects(id=id).first()
    if comment.auteur != user:
        request.session["error"] = "Vous ne disposez pas des droits de suppression sur ce commentaire !!!"
        return redirect(f"/profil_utilisateur/{from_id}")
    comment.delete()
    request.session["success"] = "Commentaire supprimé avec succés !!!"
    return redirect(f"/profil_utilisateur/{from_id}")

def delete_comment4(request,id, from_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    comment = Commentaire.objects(id=id).first()
    if comment.auteur != user:
        request.session["error"] = "Vous ne disposez pas des droits de suppression sur ce commentaire !!!"
        return redirect(f"/mes_plaintes/{from_id}/view")
    comment.delete()
    request.session["success"] = "Commentaire supprimé avec succés !!!"
    return redirect(f"/mes_plaintes/{from_id}/view")

def chats_sans_conversation(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user

    conversations = Conversation.objects(Q(user1=user) | Q(user2=user)).order_by('-date_modification')
    context["conversations"] = conversations

    context["conversation"] = None
    context["correspondant"] = None

    return render(request, "app/chats/all_chats.html", context)

def chats_avec_conversation(request, correspondant_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user

    conversations = Conversation.objects(Q(user1=user) | Q(user2=user)).order_by('-date_modification')
    context["conversations"] = conversations

    correspondant = Utilisateur.objects(id=correspondant_id).first()
    conversation = Conversation.objects(
        (Q(user1=user, user2=correspondant)) | (Q(user1=correspondant, user2=user))
    ).first()

    if not conversation:
        conversation = Conversation(user1=user, user2=correspondant)
        conversation.save()

    context["correspondant"] = correspondant
    context["conversation"] = conversation
    
    if request.POST:
        text = request.POST.get("text", None)
        if not text:
            request.session["error"] = "Le texte est obligatoire !!!"
            return redirect(f"/chats/{correspondant_id}")
        message = Message(conversation = conversation, sender=user, text=text.strip())
        message.save()
        return redirect(f"/chats/{correspondant_id}")

    return render(request, "app/chats/all_chats.html", context)

def delete_message(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    message = Message.objects(id=id).first()
    if message:
        url = f"/chats/{message.conversation.get_other_user(user).id}"
        if message.sender != user:
            request.session["error"] = "Vous n'êtes pas autorisés à supprimer ce message !!!"
            return redirect(url)
        message.delete()
        request.session["success"] = "Message supprimé avec succès !!!"
        return redirect(url)
    else:
        return redirect("/deconnexion")

def publications(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    return render(request, "app/pubs/all.html", context)

def utilisateurs(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects()
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def utilisateurs_citoyen(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects(role="CITOYEN")
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def utilisateurs_autorite(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects(role="AUTORITE")
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def utilisateurs_technicien(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects(role="TECHNICIEN")
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def utilisateurs_admin(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects(role="ADMIN")
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def utilisateurs_sys(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits requis pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    
    users = Utilisateur.objects(role="SYS")
    context["users"] = users
    counters = {}
    counters["all"] = users.count()
    counters["citoyens"] = Utilisateur.objects(role="CITOYEN").count()
    counters["autorites"] = Utilisateur.objects(role="AUTORITE").count()
    counters["techniciens"] = Utilisateur.objects(role="TECHNICIEN").count()
    counters["admin"] = Utilisateur.objects(role="ADMIN").count()
    counters["sys"] = Utilisateur.objects(role="SYS").count()
    context["counters"] = counters
    return render(request, "app/users/list.html", context)

def add_user(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    roles = Utilisateur().ROLES[1:4]
    context["roles"] = roles
    if request.POST:
        nom = request.POST.get("nom", None)
        prenom = request.POST.get("prenom", None)
        telephone = request.POST.get("telephone", None)
        role = request.POST.get("role", None)
        email = request.POST.get("email", None)
        
        if not (nom and prenom and telephone and role and email):
            request.session["error"] = "Tous les champs sont obligatoires !!!"
            return redirect("/add_user")
        if Utilisateur.objects(email=email).first() or Utilisateur.objects(telephone=telephone):
            request.session["error"] = "L'email et le numéro de téléphone sont uniques !!!"
            return redirect("/add_user")
        hashed_pw = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
        u = Utilisateur(
            nom = nom,
            prenom = prenom,
            telephone = telephone,
            role = role,
            email = email,
            mot_de_passe =  hashed_pw
        )
        u.save()
        request.session["success"] = "Utilisateur enregistré avec succès !!!"
        return redirect("/users")
    return render(request, "app/users/add.html", context)

def alter_user(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    
    roles = Utilisateur().ROLES[:4]
    context["roles"] = roles
    
    utilisateur = Utilisateur.objects(id=id).first()
    if not utilisateur:
        request.session["error"] = "L'utilisateur spécifié n'a pas été retrouvé !!!"
        return redirect("/users")
    context["utilisateur"] = utilisateur
    if request.POST:
        nom = request.POST.get("nom", None)
        prenom = request.POST.get("prenom", None)
        telephone = request.POST.get("telephone", None)
        role = request.POST.get("role", None)
        email = request.POST.get("email", None)
        
        if not (nom and prenom and telephone and role and email):
            request.session["error"] = "Tous les champs sont obligatoires !!!"
            return redirect("/add_user")
        if Utilisateur.objects(email=email, id__ne=utilisateur.id).first():
            request.session["error"] = "Cet email est déjà utilisé !!!"
            return redirect("/add_user")

        if Utilisateur.objects(telephone=telephone, id__ne=utilisateur.id).first():
            request.session["error"] = "Ce numéro de téléphone est déjà utilisé !!!"
            return redirect("/add_user")

        hashed_pw = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
        
        utilisateur.nom = nom
        utilisateur.prenom = prenom
        utilisateur.telephone = telephone
        utilisateur.role = role
        utilisateur.email = email
        utilisateur.mot_de_passe = hashed_pw
        utilisateur.save()
        request.session["success"] = "Utilisateur modifié avec succès !!!"
        return redirect("/users")
    return render(request, "app/users/alter.html", context)

def delete_user(request, id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    if not user.is_sys():
        request.session["error"] = "Vous ne disposez pas des droits nécessaires pour effectuer la suppression !!!"
        return redirect("/users")
    utilisateur = Utilisateur.objects(id=id)
    if not utilisateur != user:
        request.session["error"] = "Vous ne pouvez pas vous supprimer vous même !!!"
        return redirect("/users")
    utilisateur.delete()
    request.session["success"] = "Suppression de l'utilisateur effectué !!!"
    return redirect("/users")

def plaintes_autorite(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plaintes = Plainte.objects(Q(autorite=None) | Q(autorite=user))
    context["plaintes"] = plaintes
    return render(request, "app/plaintes/dash/list.html", context)

def autorite_take(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.autorite:
        request.session["error"] = "La plainte est déjà prise en charge par une autorité !!!"
        return redirect("/plaintes/autorite")
    plainte.autorite = user
    plainte.save()
    request.session['success'] = "La plainte a bien été prise en charge !!!"
    return redirect("/plaintes/autorite")

def assign_technicien(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    if not user.is_autorite():
        request.session["error"] = "Vous ne disposez pas des droits nécessaires pour accéder à cette fonctionnalité !!!"
        return redirect("/profil")
    context["user"] = user
    techniciens = Utilisateur.objects(role="TECHNICIEN")
    context["techniciens"] = techniciens
    if request.POST:
        technicien = request.POST.get("technicien", None)
        if technicien == "":
            technicien = None
        if not technicien:
            request.session["error"] = "Sélectionnez un technicien valide !!!"
            return redirect(f"/plaintes/autorite/{plainte_id}/assign")
        technicien = Utilisateur.objects(id=technicien).first()
        plainte = Plainte.objects(id=plainte_id).first()
        if plainte.technicien:
            request.session["success"] = "Réaffectation de la plainte effectuée avec succès !!!"
        else:
            request.session["success"] = "Plainte affectée avec succès !!!"
        plainte.technicien = technicien
        plainte.set_status_to_index(3) # Affectée
        plainte.save()
        return redirect(f"/plaintes/autorite")
    return render(request, "app/plaintes/dash/assign.html", context)

def plaintes_technicien(request):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plaintes = Plainte.objects(technicien=user)
    context["plaintes"] = plaintes
    return render(request, "app/plaintes/dash/list2.html", context)

def turn_into_intervention(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.technicien != user:
        request.session["error"] = "Vous ne disposez pas des droits pour effectuer cette mise à jour !!!"
        return redirect("/")
    plainte.set_status_to_index(4) # En intervention
    plainte.save()
    request.session["success"] = "Plainte mise en intervention !!!"
    return redirect("/plaintes/technicien")

def turn_into_intervention_end(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.technicien != user:
        request.session["error"] = "Vous ne disposez pas des droits pour effectuer cette mise à jour !!!"
        return redirect("/")
    plainte.set_status_to_index(6) # Réglée
    plainte.save()
    request.session["success"] = "Plainte mise en fin intervention !!!"
    return redirect("/plaintes/technicien")

def resolve_ok(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.autorite != user:
        request.session["error"] = "Vous ne disposez pas des droits pour effectuer cette mise à jour !!!"
        return redirect("/")
    plainte.set_status_to_index(7) # Résolue
    plainte.save()
    request.session["success"] = "Plainte résolue !!!"
    return redirect("/plaintes/autorite")

def resolve_not_ok(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.autorite != user:
        request.session["error"] = "Vous ne disposez pas des droits pour effectuer cette mise à jour !!!"
        return redirect("/")
    plainte.set_status_to_index(8) # Résolue
    plainte.save()
    request.session["success"] = "Plainte marquée comme non résolue !!!"
    return redirect("/plaintes/autorite")

def reject_plainte(request, plainte_id):
    if not request.session.get("user_id"):
        return redirect("connexion")

    context = {
        "error": request.session.pop("error", None),
        "success": request.session.pop("success", None)
    }

    user = Utilisateur.objects(id=request.session["user_id"]).first()
    context["user"] = user
    plainte = Plainte.objects(id=plainte_id).first()
    if plainte.autorite != user:
        request.session["error"] = "Vous ne disposez pas des droits pour effectuer cette mise à jour !!!"
        return redirect("/")
    plainte.set_status_to_index(2) # Rejetée
    plainte.save()
    request.session["success"] = "Plainte rejetée avec succès !!!"
    return redirect("/plaintes/autorite")

