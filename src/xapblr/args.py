from argparse import ArgumentParser, Action, BooleanOptionalAction

from .index import index
from .rebuild import rebuild
from .search import search_command
from .list import list_blogs
from .date_parser import parse_date

class StoreDateAction(Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, parse_date(values))


argparser = ArgumentParser(prog="xapblr")
subparsers = argparser.add_subparsers(title="Tasks")

index_parser = subparsers.add_parser(
    "index",
    help="Index a blog.",
    description="""
    Index a blog.

    By default, fetches and indexes posts newer than the latest post already in the index.
    If the blog has not previously been indexed, the index is initalised with all posts;
    subsequent calls will effect incremental updates.
    Options can be passed to re-index specific posts in the union of a set of
    post ids and a date range. Use this to make the local database reflect any
    edits made on Tumblr.
    """,
)
index_parser.set_defaults(func=index)
search_parser = subparsers.add_parser(
    "search",
    help="""Search an indexed blog. For each match, prints the indexed JSON
    object. Process further with jq.
    """,
    description="""
    Search an indexed blog.
    Query format resembles notmutt; see README for details.
    """,
)
search_parser.set_defaults(func=search_command)
rebuild_parser = subparsers.add_parser(
    "rebuild",
    help="Rebuild a local database. ",
    description="""Rebuild a local database.
    The indexing of a post may change with updates to xapblr as features are
    added and bugs fixed. As all post data is saved in the database, the index
    can be updated without the need for an expensive scraping from Tumblr.
    """,
)
rebuild_parser.set_defaults(func=rebuild)

for p in [index_parser, search_parser, rebuild_parser]:
    p.add_argument("blog", metavar="BLOG", type=str, help="The blog to index.")

since_group = index_parser.add_mutually_exclusive_group()
since_group.add_argument(
    "--full",
    action='store_true',
    help="""
    Force a full re-indexing.
    """
)
since_group.add_argument(
    "--since",
    metavar="DATETIME",
    action=StoreDateAction,
    help="""
    Re-index posts made since %(metavar)s. Default: the time of the latest indexed
    post.
    """,
)
index_parser.add_argument(
    "--until",
    action=StoreDateAction,
    metavar="DATETIME",
    help="Re-index posts made until %(metavar)s. Default: now",
)
index_parser.add_argument(
    "id",
    nargs="*",
    help=""" Explicitly re-index the post with this id.""",
)
index_parser.add_argument(
    "--stemmer",
    help="""
    xapian stemmer to use for indexing.  If absent, posts are indexed verbatim.
    See xapian docs
    (https://xapian.org/docs/apidoc/html/classXapian_1_1Stem.html) for possible
    values
    """,
    default=None,
)
index_parser.add_argument(
    "--throttle",
    action=BooleanOptionalAction,
    default=True,
    help="""
    Whether to throttle requests to respect Tumblr's API rate limit (1000/hour
    or 5000/calendar day, EST.)
    """,
)

search_parser.add_argument(
    "--verbatim",
    action=BooleanOptionalAction,
    help="""
    Whether to match words exactly. If set to False, use xapian's stemmer.
    """,
    default=True,
)
search_parser.add_argument(
    "--sort",
    choices=["newest", "oldest", "relevance"],
    help="How to sort search results.",
    default="newest",
)
search_parser.add_argument(
    "search-term",
    nargs="+",
    help="A search term; see README.",
    type=str,
)


server_parser = subparsers.add_parser(
    "server",
    help="Start web interface.",
    description="""
    Start web interface.
    """,
)
server_parser.add_argument(
    "-p",
    "--port",
    type=int,
    metavar="PORT",
    help="Listen on port %(port)s",
)

list_parser = subparsers.add_parser("list", help="List indexed blogs")
list_parser.set_defaults(func=list_blogs)
