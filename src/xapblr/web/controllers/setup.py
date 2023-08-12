from ...models.user import StatusE, PrivilegeE, Status, Privilege, User
from ...db import get_db

from sqlalchemy import func, select
from time import time

def setup():
    db = get_db()
    with db.session() as session:
        statuses = get_statuses(session)
        privileges = get_privileges(session)
        [session.add(s) for s in statuses.values() if s.id is None]
        [session.add(p) for p in privileges.values() if p.id is None]
        n_users = session.query(func.count(User.id)).scalar()
        if n_users == 0:
            default_account = User(
                name="admin",
                password="password",
                email="admin@xapblr.io",
                registered=int(time()),
                last_seen=None,
                max_invites=0,
                status=statuses[StatusE.ACTIVE],
                privilege=privileges[PrivilegeE.ROOT],
            )
            session.add(default_account)
        session.commit()

def get_statuses(session):
    q = select(Status).where(Status.name.in_(StatusE))
    out = {}
    for s in session.scalars(q):
        out[s.name] = s
    for k in StatusE:
        if k not in out.keys():
            out[k] = Status(name=k)
    return out

def get_privileges(session):
    q = select(Privilege).where(Privilege.name.in_(PrivilegeE))
    out = {}
    for s in session.scalars(q):
        out[s.name] = s
    for k in PrivilegeE:
        if k not in out.keys():
            out[k] = Privilege(name=k)
    return out
