from time import time
from datetime import datetime
from json import dumps
from math import ceil
import pytumblr
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import sys
from xapian import (
    DocNotFoundError,
    Document,
    Stem,
    TermGenerator,
    sortable_serialise,
)

from time import sleep

from urllib.parse import urlparse

from .blog import BlogIndex
from .config import config
from .models.image import Image, ImageState, ImageInPost
from .db import get_db as get_sqldb
from .search import get_latest
from .utils import (
    get_author,
    get_unique_term,
    encode_tag,
    format_timestamp,
    prefixes,
    value_slots,
)


def index_text(block, tg, out_data):
    tg.index_text(block["text"])


def index_link(block, tg, out_data):
    doc = tg.get_document()
    url_prefix = "https://href.li/?"
    url = block["url"].removeprefix(url_prefix)
    domain = urlparse(url).hostname
    while True:
        doc.add_term(prefixes["link"] + domain)
        try:
            sep = domain.index(".")
            domain = domain[sep + 1 :]
        except ValueError:
            break
    tg.index_text(block["description"])


def index_image(block, tg, out_data):
    for m in block["media"]:
        if m.get("type", None) == "image/gif":
            tg.get_document().add_term(prefixes["has"] + "gif")
            break
    for m in block["media"]:
        media_key = m.get("media_key", None)
        if media_key:
            tg.get_document().add_term(prefixes["media"] + media_key)
            break

    mw = 0
    url = None
    for m in block["media"]:
        if m["width"] > mw:
            url = m["url"]
        if m.get("has_original_dimensions", False):
            break
    if media_key is None:
        media_key = urlparse(url).path
    out_data["images"][media_key] = {"media_key": media_key, "url": url}

    try:
        tg.index_text(block["alt_text"])
    except KeyError:
        pass


def index_poll(block, tg, out_data):
    tg.index_text(block["question"])
    for a in block["answers"]:
        tg.index_text(a["answer_text"])


block_indexers = {
    "text": index_text,
    "link": index_link,
    "image": index_image,
    "poll": index_poll,
}


def index_content(post, tg, out_data):
    doc = tg.get_document()
    for block in post["content"]:
        if block["type"] != "text":
            has_term = prefixes["has"] + block["type"]
            doc.add_term(has_term)
        try:
            block_indexers[block["type"]](block, tg, out_data)
        except KeyError:
            pass
    doc.add_term(prefixes["author"] + get_author(post))


def index_post(post, tg):
    doc = Document()
    tg.set_document(doc)
    # data for post-processing after seeing the whole post
    out_data = {"images": {}}

    if len(post["trail"]) > 0:
        op = get_author(post["trail"][0])
    else:
        op = post["blog"]["name"]
    doc.add_term(prefixes["op"] + op)

    for t in post["trail"]:
        index_content(t, tg, out_data)
    index_content(post, tg, out_data)

    for t in post["tags"]:
        doc.add_term(encode_tag(t))

    doc.add_value(value_slots["timestamp"], sortable_serialise(post["timestamp"]))
    doc.set_data(dumps(post))

    id_term = "Q" + str(post["id"])
    doc.add_boolean_term(id_term)

    return (id_term, doc, out_data)


def index(args):
    try:
        api_key = config["api_key"]
    except KeyError:
        sys.exit("No API key configured. Exiting.")

    client = pytumblr.TumblrRestClient(**api_key)
    kwargs = {}
    if args.until is not None:
        kwargs["before"] = args.until

    n = 0
    print(f"Indexing {args.blog}... ", end="")
    try:
        blog = client.blog_info(args.blog)["blog"]
    except KeyError:
        print()
        print("Blog does not exist or API key owner is blocked by it.", file=sys.stderr)
        # TODO: this should probably throw instead
        return
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

    tg = TermGenerator()
    if args.stemmer is not None:
        tg.set_stemmer(Stem(args.stemmer))

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

    pages = 1
    commit_every = 10
    images = {}
    with BlogIndex(args.blog, "w") as db:
        while fetch:
            response = client.posts(args.blog, npf=True, **kwargs)
            posts = response["posts"]

            if len(posts) == 0:
                break
            n += len(posts)

            for p in posts:
                (id_term, post_doc, out_data) = index_post(p, tg)
                did = db.replace_document(id_term, post_doc)
                append_images(images, out_data, did)
                kwargs["before"] = p["timestamp"]

            if pages % commit_every == 0:
                print("*", end="", flush=True)
                db.commit()
                queue_images(db, images, args.blog)
                images = {}
            else:
                print(".", end="", flush=True)
            if "_links" not in response.keys():
                break
            if args.since is not None and args.since >= kwargs["before"]:
                break

            pages += 1
            sleep(throttle)

        queue_images(db, images, args.blog)
    print()
    print(f"Done; indexed {n} posts.")


def queue_images(db, imgs, blog):
    sqldb = get_sqldb()
    with sqldb.session() as s:
        existing_imgs_q = (
            select(Image)
            .options(joinedload(Image.posts))
            .where(Image.media_key.in_(imgs.keys()))
        )
        img_objs = {}
        tg = TermGenerator()
        for img in s.scalars(existing_imgs_q).unique():
            ps = [(p.blog, p.post_id) for p in img.posts]
            for did in imgs[img.media_key]["posts"]:
                if (blog, did) not in ps:
                    img.posts.append(ImageInPost(blog=blog, post_id=did, image=img))
                add_caption_to_doc(db, did, tg, img.caption)
            img_objs[img.media_key] = img

        new_img_objs = [
            Image(
                media_key=v["media_key"],
                url=v["url"],
                state=ImageState.AVAILABLE,
                created=int(time()),
                posts=[ImageInPost(blog=blog, post_id=did) for did in v["posts"]],
            )
            for k, v in imgs.items()
            if k not in img_objs.keys()
        ]
        s.add_all(new_img_objs)
        s.commit()


def append_images(images, out_data, did):
    for k, v in out_data["images"].items():
        if k in images.keys():
            images[k]["posts"].append(did)
        else:
            images[k] = v
            images[k]["posts"] = [did]


def add_caption_to_doc(db, did, tg, caption):
    if caption is None:
        return
    try:
        doc = db.get_document(did)
    except DocNotFoundError:
        return
    id_term = get_unique_term(doc)
    tg.set_document(doc)
    tg.index_text(caption, 1, prefixes["image"])
    db.replace_document(id_term, doc)
