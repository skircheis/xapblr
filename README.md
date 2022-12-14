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
`xapblr` requires a a Tumblr API key, which you can obtain [by registering the app with Tumblr](https://www.tumblr.com/oauth/apps) and then [obtaining authentication data](https://api.tumblr.com/console/calls/user/info).
`xapblr` expects to find this authentication data in `$XDG_CONFIG_HOME/xapblr/APIKEY`, in JSON format like so:
```json
{
    "consumer_key": <consumer_key>,
    "consumer_secret": <consumer_secret>,
    "oauth_token": <oauth_token>,
    "oauth_secret": <oauth_secret>
}
```
Although this is not enforced, for security the `APIKEY` file should be readable only by its
owner.

`xapblr` stores its data in `$XDG_DATA_HOME/share/xapblr/`; by default this
should be `~/.local/share/xapblr`.

`systemd` units are provided for regular re-indexing.

## Usage

See `xapblr --help` for detailed usage, and `SEARCH.md` for how to form search
queries.


## Rebuilding

As `xapblr` is developed the indexing of posts may change to fix bugs or add
features. To allow for this all post data is saved in the database, meaning the
index can be rebuilt from local data only.

`xapblr` uses semantic versioning and changes to indexing imply a minor version increase.
It is recommended to run `xapblr rebuild` after each minor version increase.

## Web interface

`xapblr` provides a web interface for convenience.  A *development* version can
be launched with `xapblr server`; By default it resides on `localhost:5000`.

A future version will provide a *production* version, suitable to run e.g. with
`systemd`.

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

## Dependencies: ##
 * Python 3
 * `pytumblr`
 * `xapian`
 * `flask` and `flask-assets` for the web interface)
 * `lark`
