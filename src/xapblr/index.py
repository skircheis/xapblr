import pytumblr
import xapian

from time import sleep

from urllib.parse import quote as urlencode

from .utils import get_api_key, get_db

key_fname = "APIKEY"

prefixes = {
    "content": "XC",
    "op": "XOP",
    "author": "A",
    "id": "Q",
    "tag": "K",
    "url": "U",
}

def get_author(post):
    try:
        return post["blog"]["name"]
    except KeyError:
        return post["broken_blog_name"]

def index_content(post, tg):
    [
        tg.index_text(c["text"])
        for c in post["content"]
        if c["type"] == "text"
    ]
    doc = tg.get_document()
    doc.add_term(prefixes["author"] + get_author(post))

def index_post(post, tg):
    doc = xapian.Document()
    tg.set_document(doc)

    if len(post["trail"]) > 0 :
        op = get_author(post)
    else:
        op = post["blog"]["name"]
    doc.add_term(prefixes["op"] + op)

    for t in post["trail"]:
        index_content(t, tg)
    index_content(post, tg)

    for t in post["tags"]:
        # xapian will never put a space in a term but we can just urlencode
        doc.add_term(prefixes["tag"] + urlencode(t))

    doc.add_term(prefixes["url"] + post["post_url"])

    id_term = u"Q" + str(post["id"])
    doc.add_boolean_term(id_term)

    return (id_term, doc)

def index(args):

    api_key = get_api_key()
    db = get_db(args.blog, "w")
    client = pytumblr.TumblrRestClient(**api_key)
    tg = xapian.TermGenerator()
    if args.stemmer is not None:
        tg.set_stemmer(xapian.Stem(args.stemmer))

    kwargs = {}
    if args.until is not None:
        kwargs["before"] = args.until

    n = 0
    print(f"Indexing {args.blog}", end="", flush=True)
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
