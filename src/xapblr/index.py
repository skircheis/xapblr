from json import dumps
import pytumblr
from xapian import (
    Document,
    Enquire,
    Query,
    Stem,
    TermGenerator,
    sortable_serialise,
    sortable_unserialise,
)

from time import sleep

from urllib.parse import quote as urlencode

from .search import get_latest
from .utils import get_api_key, get_db, format_timestamp, prefixes

def get_author(post):
    try:
        return post["blog"]["name"]
    except KeyError:
        return post["broken_blog_name"]


def index_content(post, tg):
    [tg.index_text(c["text"]) for c in post["content"] if c["type"] == "text"]
    doc = tg.get_document()
    doc.add_term(prefixes["author"] + get_author(post))


def index_post(post, tg):
    doc = Document()
    tg.set_document(doc)

    if len(post["trail"]) > 0:
        op = get_author(post["trail"][0])
    else:
        op = post["blog"]["name"]
    doc.add_term(prefixes["op"] + op)

    for t in post["trail"]:
        index_content(t, tg)
    index_content(post, tg)

    for t in post["tags"]:
        # xapian will never put a space in a term but we can just urlencode
        doc.add_term(prefixes["tag"] + urlencode(t))

    doc.add_value(0, sortable_serialise(post["timestamp"]))
    doc.set_data(dumps(post))

    id_term = "Q" + str(post["id"])
    doc.add_boolean_term(id_term)

    return (id_term, doc)


def index(args):

    api_key = get_api_key()
    client = pytumblr.TumblrRestClient(**api_key)
    kwargs = {}
    if args.until is not None:
        kwargs["before"] = args.until

    n = 0
    print(f"Indexing {args.blog}... ", end="")
    if args.full:
        print("Performing full re-index...")
    else:
        latest_ts = get_latest(args.blog)
        if latest_ts is None:
            print("Database is empty, indexing until beginning...")
        else:
            print(f"Latest seen post is {format_timestamp(latest_ts)}...")
            if args.since is None:
                args.since = latest_ts

    db = get_db(args.blog, "w")
    tg = TermGenerator()
    if args.stemmer is not None:
        tg.set_stemmer(Stem(args.stemmer))


    while True:
        posts = client.posts(args.blog, npf=True, **kwargs)

        if len(posts["posts"]) == 0:
            break
        n += len(posts["posts"])

        for p in posts["posts"]:
            (id_term, post_doc) = index_post(p, tg)
            db.replace_document(id_term, post_doc)
            kwargs["before"] = p["timestamp"]

        print(".", end="", flush=True)
        if "_links" not in posts.keys():
            break

        if args.since is not None and args.since >= kwargs["before"]:
            break

        if args.throttle:
            sleep(3.6)

    print()
    print(f"Done; indexed {n} posts.")
