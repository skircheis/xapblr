from argparse import ArgumentParser, Action, BooleanOptionalAction
from platform import node

from .clip import clip_cmd
from .config import config
from .index import index
from .list import list_cmd
from .rebuild import rebuild
from .render import renderers
from .search import search_command
from .server import server
from .date_parser import parse_date
from .utils import fix_date_range


class StoreDateAction(Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, parse_date(values))


argparser = ArgumentParser(prog="xapblr")
subparsers = argparser.add_subparsers(title="Tasks", required=True)

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
    Query format resembles notmuch; see README for details.
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
    action="store_true",
    help="""
    Force a full re-indexing.
    """,
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
    "--renderer",
    choices=list(renderers.keys()),
    help="""
    Output format. Json dumps the indexed as a JSON object. Plain, md, html
    approximate Tumblr's own rendering with increasing (but low, even for html)
    fidelity. Finally, embed queries Tumblr's OEmbed enpoint for the embedded
    HTML. It is therefore MUCH slower than formats that rely on locally cached
    data and not suitable for large sets of matches.
    Default: %(default)s.
    """,
    default="json",
)
search_parser.add_argument(
    "--width",
    type=int,
    metavar="W",
    help="""
    Target output width. With the plain text renderer, wraps lines after
    %(metavar)s characters. With the markdown renderer, chooses images as close
    to %(metavar)s pixels wide as possible. Has no effect on json, html, or
    embed output.
    Default: 80 (plain), 540 (md).
    """,
)
search_parser.add_argument(
    "-l",
    "--limit",
    type=int,
    help="""
    Return at most %(metavar)s results
    """,
    metavar="N",
    default=None,
)
search_parser.add_argument(
    "-o",
    "--offset",
    type=int,
    metavar="N",
    help="""
    Skip the first %(metavar)s results
    """,
    default=0,
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
    "search",
    metavar="search-term",
    nargs="+",
    help="A search term; see README.",
    type=fix_date_range,
)


server_parser = subparsers.add_parser(
    "server",
    help="Start web interface.",
    description="""
    Start web interface. Intended only for development.
    For production usage, use the xapblr_web service.
    """,
)
server_parser.set_defaults(func=server)
server_parser.add_argument(
    "--debug",
    action="store_true",
    help="""
    Enable Flask's debug mode. Major security risk, never use in production!
    """,
)
server_parser.add_argument(
    "--host",
    type=str,
    help="Host to bind to.",
)
server_parser.add_argument(
    "-p",
    "--port",
    type=int,
    metavar="PORT",
    help="Listen on port %(metavar)s",
)

list_parser = subparsers.add_parser("list", help="List indexed blogs")
list_parser.set_defaults(func=list_cmd)

clip_parser = subparsers.add_parser("clip", help="Launch a CLIP agent.")
clip_parser.set_defaults(func=clip_cmd)
clip_parser.add_argument("server", help="The server profile to communicate with.")
try:
    default_agent_id = config["clip_agent"]["agent_id"]
except KeyError:
    default_agent_id = node()
clip_parser.add_argument(
    "--agent-id",
    dest="agent_id",
    metavar="ID",
    help="Agent ID to use. Default: %(default)s",
    default=default_agent_id,
)
clip_parser.add_argument(
    "--sleep",
    metavar="N",
    help="After finishing all available tasks, sleep N seconds before checking for new tasks. Default: %(default)s",
    default=config["clip_agent"]["sleep"],
    type=int,
)
