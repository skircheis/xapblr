from json import loads, dumps
from xapian import (
    Database,
    Enquire,
    FieldProcessor,
    Query,
    QueryParser,
    sortable_unserialise,
)
from urllib.parse import quote as urlencode

from .utils import format_timestamp, get_db, prefixes


def search_command(args):
    for m in search(args):
        print(dumps(m))


class TagProcessor(FieldProcessor):
    def __call__(self, args):
        return Query(prefixes["tag"] + urlencode(args))


def search(args):

    db = get_db(args.blog, "r")
    qp = QueryParser()
    qp.set_stemming_strategy(QueryParser.STEM_NONE)
    qp.set_default_op(Query.OP_AND)
    qp.add_boolean_prefix("author", prefixes["author"])
    qp.add_boolean_prefix("op", prefixes["op"])
    qp.add_boolean_prefix("tag", TagProcessor())
    qstr = " ".join(getattr(args, "search-term"))
    query = qp.parse_query(qstr)
    enq = Enquire(db)
    if args.sort == "newest":
        enq.set_sort_by_value_then_relevance(0, True)
    elif args.sort == "oldest":
        enq.set_sort_by_value_then_relevance(0, False)
    elif args.sort == "relevance":
        pass
    enq.set_query(query)
    offset = 0
    pagesize = 100
    count = 0
    while True:
        matches = enq.get_mset(offset, pagesize)
        if matches.empty():
            break
        for match in matches:
            doc = match.document
            post_json = doc.get_data().decode("utf-8")
            yield loads(post_json)
            count += 1
            if args.limit is not None and count >= args.limit:
                return
        offset += pagesize


def get_latest(src):
    if type(src) == str:
        db = get_db(src)
    elif isinstance(src, Database):
        db = src
    else:
        raise TypeError(f"expected xapian database or string, got {type(src)}")
    if db.get_doccount() == 0:
        return None

    enq = Enquire(db)
    enq.set_query(Query.MatchAll)
    enq.set_sort_by_value_then_relevance(0, True)
    latest = enq.get_mset(0, 1)[0].document
    return sortable_unserialise(latest.get_value(0))
