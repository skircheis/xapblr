from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload

from xapblr.config import config
from xapblr.index import add_caption_to_doc
from xapblr.models.image import Image, ImageState, ImageInPost
from xapblr.db import db
from xapblr.utils import get_db, get_unique_term, prefixes

from time import time_ns, time
from xapian import DocNotFoundError, TermGenerator


def clip_accept(imgs):
    dbs = {}
    tg = TermGenerator()
    with db.session() as s:
        q = (
            select(Image)
            .options(joinedload(Image.posts))
            .where(Image.id.in_(imgs.keys()) & (Image.state == ImageState.ASSIGNED))
            # the second condition ensures that only the first submission of a
            # caption will be saved
        )
        for img in s.scalars(q).unique():
            img.state = ImageState.CAPTIONED
            img.caption = imgs[img.id]["caption"]
            img.captioned = int(time())

            for p in img.posts:
                if p.blog not in dbs.keys():
                    dbs[p.blog] = get_db(p.blog, "w")
                x = dbs[p.blog]
                add_caption_to_doc(x, p.post_id, tg, img.caption)
        s.commit()


def clip_offer(args):
    out = {}
    with db.session() as s:
        # If an image was assigned more than timeout seconds ago, and has not
        # been captioned yet, it is assumed that the assignee will not complete
        # the job. We should mark the image as available for other agents.
        conn = s.connection()
        refresh = (
                update(Image)
                .where(
                    (Image.state == ImageState.ASSIGNED)
                    & (Image.assigned + config["clip"]["timeout"] < int(time()))
                    )
                .values(state = ImageState.AVAILABLE)
                )
        conn.execute(refresh)

        q = (
            select(Image)
            .where(Image.state == ImageState.AVAILABLE)
            .order_by(Image.created)
            .limit(config["clip"]["batch_size"])
        )
        n = (
            s.query(func.count(Image.id))
            .where(Image.state == ImageState.AVAILABLE)
            .scalar()
        )
        imgs = s.scalars(q)
        out["available"] = n
        out["images"] = []
        for i in imgs:
            i.state = ImageState.ASSIGNED
            i.agent = args["agent"]
            i.assigned = int(time())
            out["images"].append({"id": i.id, "media_key": i.media_key, "url": i.url})
        s.commit()
    return out
