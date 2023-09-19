from datetime import datetime
from json import loads
from xapian import (
    Database,
    Enquire,
    FieldProcessor,
    Query,
    QueryParser,
    QueryParserError,
    RangeProcessor,
    sortable_serialise,
    sortable_unserialise,
)

from .date_parser import parse_date
from .render import renderers
from .utils import get_db, encode_tag, prefixes, value_slots


def search_command(args):
    res = search(args)
    try:
        print("An error occured: " + res[0]["error"])
        return
    except KeyError:
        pass
    for m in res[1]:
        out = renderers[args.renderer](m, args)
        print(out)


class ImageProcessor(FieldProcessor):
    pass


class TagProcessor(FieldProcessor):
    def __call__(self, args):
        return Query(encode_tag(args))


class DateRangeProcessor(RangeProcessor):
    def __init__(self, slot, prefix):
        super(DateRangeProcessor, self).__init__(slot, prefix)
        self.slot = slot

    def __call__(self, begin, end):
        begin, end = begin.decode("utf8"), end.decode("utf8")
        try:
            if len(begin) == 0:
                begin = 0.0
            else:
                begin = parse_date(begin)
            if len(end) == 0:
                end = datetime.now().timestamp()
            else:
                end = parse_date(end)
            begin, end = sortable_serialise(begin), sortable_serialise(end)
        except ValueError as e:
            raise QueryParserError(str(e))
        return Query(Query.OP_VALUE_RANGE, self.slot, begin, end)

class XapblrQueryParser(QueryParser):
    def __init__(self):
        QueryParser.__init__(self)
        self.set_stemming_strategy(QueryParser.STEM_NONE)
        self.set_default_op(Query.OP_AND)

        self.add_rangeprocessor(DateRangeProcessor(value_slots["timestamp"], "date:"))

        [
            self.add_boolean_prefix(p, prefixes[p])
            for p in ["author", "has", "link", "media", "op"]
        ]
        self.add_prefix("image", prefixes["image"])
        self.add_boolean_prefix("tag", TagProcessor())


def search(args):
    """
    Returns a tuple (meta, iter) where meta is a dict containing meta
    information about the MSet, and iter is an iterator over the matches
    """

    offset = args.offset or 0
    pagesize = args.limit or 50
    meta = {
        "offset": offset,
        "pagesize": pagesize,
    }

    db = get_db(args.blog, "r")
    qp = XapblrQueryParser()

    qstr = " ".join(args.search)
    try:
        query = qp.parse_query(qstr)
    except QueryParserError as e:
        meta["matches"] = 0
        meta["error"] = str(e)
        return (meta, iter([]))

    enq = Enquire(db)
    if args.sort == "newest":
        enq.set_sort_by_value_then_relevance(0, True)
    elif args.sort == "oldest":
        enq.set_sort_by_value_then_relevance(0, False)
    elif args.sort == "relevance":
        pass
    enq.set_query(query)
    matches = enq.get_mset(offset, pagesize)
    meta["matches"] = matches.get_matches_estimated()
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
