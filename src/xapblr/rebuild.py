from json import loads
from xapian import Enquire, Query, TermGenerator
from .index import index_post
from .utils import get_db


def rebuild(args):
    db = get_db(args.blog, "w")
    count = db.get_doccount()
    if count == 0:
        return

    tg = TermGenerator()
    enq = Enquire(db)
    enq.set_query(Query.MatchAll)
    enq.set_sort_by_value_then_relevance(0, True)
    offset = 0
    perpage = 1000
    print(f"Rebuilding {count} posts (. = {perpage} posts)")
    while True:
        matches = enq.get_mset(offset, perpage)
        if matches.empty():
            break
        for m in matches:
            old = m.document
            (id_term, post_doc) = index_post(loads(old.get_data()), tg)
            db.replace_document(id_term, post_doc)
        offset += perpage
        print(".", end="", flush=True)
    print()
    print("Done.")
