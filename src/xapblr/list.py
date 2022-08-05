from xapian import Database
from .utils import get_db_dir, get_db, format_timestamp
from .search import get_latest


def list_blogs(args):
    for child in get_db_dir().iterdir():
        if child.is_dir():
            try:
                db = Database(str(child))
            except Exception:
                continue
            count = db.get_doccount()
            latest_ts = get_latest(db)
            print(f"{child.name}: {count} indexed posts;", end=" ")
            if latest_ts is not None:
                print(f"latest seen post: {format_timestamp(latest_ts)}")
            else:
                print("empty database")
