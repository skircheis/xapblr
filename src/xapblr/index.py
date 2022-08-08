from time import time
from datetime import datetime
from json import dumps
from math import ceil
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

from urllib.parse import quote as urlencode, urlparse

from .search import get_latest
from .utils import get_api_key, get_author, get_db, format_timestamp, prefixes

def index_text(block, tg):
    tg.index_text(block["text"])

def index_link(block, tg):
    doc = tg.get_document()
    url_prefix = "https://href.li/?"
    url = block["url"].removeprefix(url_prefix)
    domain = urlparse(url).hostname
    while True:
        doc.add_term(prefixes["link"] + domain)
        try:
            sep = domain.index(".")
            domain = domain[sep+1:]
        except ValueError:
            break
    tg.index_text(block["description"])

def index_image(block, tg):
    try:
        tg.index_text(block["alt_text"])
    except KeyError:
        pass


block_indexers = {
    "text": index_text,
    "link": index_link,
    "image": index_image,
}


def index_content(post, tg):
    for block in post["content"]:
        try:
            block_indexers[block["type"]](block, tg)
        except KeyError:
            pass
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
        doc.add_term(prefixes["tag"] + urlencode(t.lower()))

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
    full = False
    if args.full:
        print("Performing full re-index...")
        full = True
    else:
        latest_ts = get_latest(args.blog)
        if latest_ts is None:
            print("Database is empty, indexing until beginning...")
            full = True
        else:
            print(f"Latest seen post is {format_timestamp(latest_ts)}...")
            if args.since is None:
                args.since = latest_ts

    db = get_db(args.blog, "w")
    tg = TermGenerator()
    if args.stemmer is not None:
        tg.set_stemmer(Stem(args.stemmer))

    blog = client.blog_info(args.blog)["blog"]
    fetch = True
    if args.since is not None and args.since >= blog["updated"]:
        print(f'No new posts since {format_timestamp(blog["updated"])}', end="")
        fetch = False

    throttle = 3600 / 1000
    if args.throttle and full:
        count = blog["posts"]
        reqs = ceil(count / 20)
        # rate limit: 5000 requests per calendary day (EST) or 1000 requests
        # per hour.
        daily_limit = 5000
        if reqs >= daily_limit:
            print(
                f"Blog has {count} posts, need {reqs} requests; throttling down to {daily_limit} / day."
            )
            throttle = 3600 * 24 / daily_limit
        eta = time() + reqs * throttle
        eta_hf = format_timestamp(eta)
        eta_locale = datetime.fromtimestamp(eta).strftime("%c")
        print(f"ETA: {eta_hf} ({eta_locale})")
    if not args.throttle:
        throttle = 0

    while fetch:
        response = client.posts(args.blog, npf=True, **kwargs)
        posts = response["posts"]

        if len(posts) == 0:
            break
        n += len(posts)

        for p in posts:
            (id_term, post_doc) = index_post(p, tg)
            db.replace_document(id_term, post_doc)
            kwargs["before"] = p["timestamp"]

        print(".", end="", flush=True)
        if "_links" not in response.keys():
            break
        if args.since is not None and args.since >= kwargs["before"]:
            break

        sleep(throttle)

    print()
    print(f"Done; indexed {n} posts.")
