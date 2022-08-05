xapblr
======

Locally index Tumblr blogs in a xapian database for advanced searching.
Think `notmuch`, but for Tumblr.

## Setup

Install with
```sh
    python -m build --wheel --no-isolation
    python -m installer dist/*.whl
```
`xapblr` requires a a Tumblr API key, which you can obtain [by registering the app with Tumblr](https://www.tumblr.com/oauth/apps).
`xapblr` expects to find this key in `$XDG_CONFIG_HOME/xapblr/APIKEY`; although
this is not enforced, for security this file should be readable only by its
owner.

`xapblr` stores its data in `$XDG_DATA_HOME/share/xapblr/`; by default this
should be `~/.local/share/xapblr`.

systemd units are provided for regular re-indexing.

## Initialization and rate-limiting

The Tumblr API is rate-limited to 1000 requests per hour and 5000 requests per
calendar day (EST). Since the `/posts` endpoint returns at most 20 posts per
requests initializing a large blog can easily take several hours, if not more
than a day. `xapblr init` automatically throttles to respect rate limits.

Incrementally fetching and indexing new posts is trivially cheap: the post
limit is 250 per day. Daily fetching therefore uses at most 13 requests, and
even hourly fetching is cheap.

However, continually reindexing an entire blog to reflect any edits that may
have been made is obviously prohibitively expensive. If you wish to update
posts that you know have been edited on Tumblr, pass suitable options to
`xapblr index`.

## Search terms

## General

`xapblr`'s search terms generally match those of `notmuch`. If you know how
to work with `notmuch`, you already know most of `xapblr`.

The boolean operators `OR` and `AND`, `NOT`, and parentheses `()` can be used to combine multiple predicates.
The default connective is `AND`.

## Predicates

* `body:<word-or-quoted-phrase>`
    Match terms in the bodies of posts.
* `op:<blog-name>`
    Match posts where the root post is from <blog-name>.
* `from:<blog-name>`
    Match posts where the any post in the reblog chain is from <blog-name>.
* `tag:<tag>`
Match posts tagged `#<tag>`
* `date:<since>..<until> or date:<date>`
    Match posts made between `<since>` and `<until>`

    xapblr aims to support the same date and time search as `notmuch`; see the `notmuch` documentation for details.

## Dependencies: ##
 * Python 3
 * `pytumblr`
 * `xapian`
 * `lark`
