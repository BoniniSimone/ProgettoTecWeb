# accounts/permissions.py

GROUP_SEGRETARIO = "segretario"
GROUP_GESTORE = "gestore_film"

STAFF_GROUPS = [GROUP_SEGRETARIO, GROUP_GESTORE]


def has_any_group(user, names):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__in=names).exists()


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def is_operational_staff(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or has_any_group(user, STAFF_GROUPS)


def is_cliente(user):
    return user.is_authenticated and not is_operational_staff(user)


def role(user):
    if not user.is_authenticated:
        return "anon"
    if user.is_superuser:
        return "admin"
    if has_any_group(user, [GROUP_GESTORE]):
        return "gestore_film"
    if has_any_group(user, [GROUP_SEGRETARIO]):
        return "segretario"
    if user.is_staff:
        return "staff"
    return "cliente"


def can_manage_users(user):
    return role(user) in {"segretario", "gestore_film", "admin"}


def can_delete_user(actor, target):
    """
    Regole:
    - segretario: può eliminare solo clienti
    - gestore_film: può eliminare clienti e segretari
    - admin (superuser): può eliminare clienti, segretari, gestori
    - nessuno può eliminare superuser o sé stesso
    """
    if not actor.is_authenticated:
        return False
    if target == actor:
        return False
    if target.is_superuser:
        return False

    a = role(actor)
    t = role(target)

    if a == "segretario":
        return t == "cliente"
    if a == "gestore_film":
        return t in {"cliente", "segretario"}
    if a == "admin":
        return t in {"cliente", "segretario", "gestore_film", "staff"}

    return False

# Mi server per utilizzare {{staff_mode }} nei template
def staff_flags(request):
    return {"staff_mode": is_operational_staff(request.user)}
