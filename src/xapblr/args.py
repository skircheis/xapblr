from argparse import ArgumentParser

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
search_parser = subparsers.add_parser(
    "search", help="Search an indexed blog.",
    description="""
    Search an indexed blog.
    Query format resembles notmutt; see README for details.
    """
)
for p in [index_parser, search_parser]:
    p.add_argument("blog", metavar="BLOG", type=str, help="The blog to index.")

index_parser.add_argument(
    "--since",
    metavar="DATETIME",
    help="""
    Re-index posts made since %(metavar)s. Default: the time of the latest indexed
    post.
    """,
)
index_parser.add_argument(
    "--until",
    metavar="DATETIME",
    help="Re-index posts made until %(metavar)s. Default: now",
)
index_parser.add_argument(
    "id",
    nargs="*",
    help=""" Explicitly re-index the post with this id.""",
)

search_parser.add_argument(
    "search-term",
    nargs="+",
    help="A search term; see README.",
    type=str,
)
