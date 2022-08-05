from json import loads, dumps
from xapian import Enquire, Query, QueryParser, sortable_unserialise
from .utils import format_timestamp, get_db, prefixes

def search_command(args):
    for m in search(args):
        print(dumps(m))

def search(args):

    db = get_db(args.blog, "r")
    qp = QueryParser()
    for (name, prefix) in prefixes.items():
        qp.add_prefix(name, prefix)
    query = qp.parse_query(" ".join(getattr(args, "search-term")))
    enq = Enquire(db)
    if args.sort == "newest":
        enq.set_sort_by_value_then_relevance(0, True)
    elif args.sort == "oldest":
        enq.set_sort_by_value_then_relevance(0, False)
    elif args.sort == "relevance":
        pass
    enq.set_query(query)
    offset = 0
    pagesize = 1
    while True:
        matches = enq.get_mset(offset, pagesize)
        if matches.empty():
            break
        for match in matches:
            doc = match.document
            post_json = doc.get_data().decode("utf-8")
            yield loads(post_json)
        offset += pagesize
