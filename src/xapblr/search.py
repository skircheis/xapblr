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

from .render import renderers
from .utils import format_timestamp, get_db, prefixes


def search_command(args):
    res = search(args)
    for m in res[1]:
        out = renderers[args.renderer](m, args)
        print(out)


class TagProcessor(FieldProcessor):
    def __call__(self, args):
        return Query(prefixes["tag"] + urlencode(args.lower()))


def search(args):
    """
    Returns a tuple (meta, iter) where meta is a dict containing meta
    information about the MSet, and iter is an iterator over the matches
    """

    db = get_db(args.blog, "r")
    qp = QueryParser()
    qp.set_stemming_strategy(QueryParser.STEM_NONE)
    qp.set_default_op(Query.OP_AND)
    qp.add_boolean_prefix("author", prefixes["author"])
    qp.add_boolean_prefix("op", prefixes["op"])
    qp.add_boolean_prefix("link", prefixes["link"])
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
    offset = args.offset or 0
    pagesize = args.limit or 50
    matches = enq.get_mset(offset, pagesize)
    meta = {
        "offset": offset,
        "pagesize": pagesize,
        "matches": matches.get_matches_estimated(),
    }
    if matches.empty():
        match_iter = iter([])
    else:

        def match_iterf():
            for match in matches:
                doc = match.document
                post_json = doc.get_data().decode("utf-8")
                yield loads(post_json)
        match_iter = match_iterf()

    return (meta, match_iter)


def get_end(src, latest=True):
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
    enq.set_sort_by_value_then_relevance(0, latest)
    latest = enq.get_mset(0, 1)[0].document
    return sortable_unserialise(latest.get_value(0))


def get_latest(src):
    return get_end(src, True)


def get_earliest(src):
    return get_end(src, False)
