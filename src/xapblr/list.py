from xapian import Database
from .utils import get_data_dir, format_timestamp
from .search import get_latest, get_earliest


def list_cmd(args):
    for blog in list_blogs(args):
        print(f"{blog['name']}: {blog['count']} indexed posts;", end=" ")
        if blog["latest"] is not None:
            print(
                f"latest seen post: {format_timestamp(blog['latest'])}, earliest seen post: {format_timestamp(blog['earliest'])}"
            )
        else:
            print("empty database")


def list_blogs(args):
    for child in get_data_dir().iterdir():
        if child.is_dir():
            try:
                db = Database(str(child))
            except Exception:
                continue
            count = db.get_doccount()
            latest_ts = get_latest(db)
            earliest_ts = get_earliest(db)
            yield {
                "name": child.name,
                "count": count,
                "latest": latest_ts,
                "earliest": earliest_ts,
            }
