xapblr
======

Locally index Tumblr blogs in a xapian database for advanced searching.
Think `notmuch`, but for Tumblr.

## Setup

### Installation

If you run Arch:
```sh
git clone https://github.com/skircheis/xapblr-PKGBUILD xapblr
cd xapblr
makepkg -is
```

Otherwise clone the repository manually and build it as a Python package:
```sh
    cd xapblr
    python -m build --wheel --no-isolation
    python -m installer dist/*.whl
    sudo cp -t /etc/uwsgi config/uwsgi/xapblr.ini
```
The last step is so `uwsgi` can find `xapblr`'s web interface.

## Configuration and initialisation

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

You can now initialise the index of your blog thus:
```sh
xapblr index -full <your-blog-url>
```
This may take some time due to rate limits, see [below](#initialisation-and-rate-limiting).
The index is regularly commited to disk, so you can put this process in the background and start looking around;
try `xapblr search --help` and see `[SEARCH.md](SEARCH.MD)`.

`systemd` units are provided for regular re-indexing.
Viz.,
```sh
systemctl --user enable --now xapblr-hourly@<your-blog-url>
systemctl --user enable --now xapbl-dailyr@<your-blog-url>
```
for hourly and daily re-indexing, respectively.

## Web interface

More convenient than the command line is the web interface.
Launch it with
```sh
uwsgi --ini /etc/uwsgi/xapblr.ini
```
or as a `systemd` service
```sh
systemd --user enable --now xapblr-web
```
Then open http://localhost:5000/.

### Configuring the web interface

The web interface listens on port `5000` by default.
If you need to change this or any other `uwsgi` configuration copy the INI file (`/etc/uwsgi/xapblr.ini`), edit it as appropriate, and run from there, instead.
E.g.,
```sh
uwsgi --ini ~/.config/xapblr/uwsgi.ini
```
If running as a `systemd` service, repoint it through `systemctl --user edit xapblr-web`.

## Rebuilding

As `xapblr` is developed the indexing of posts may change to fix bugs or add
features. To allow for this all post data is saved in the database, meaning the
index can be rebuilt from local data only.

`xapblr` uses semantic versioning and changes to indexing imply a minor version increase.
It is recommended to run `xapblr rebuild` after each minor version increase.


## Initialisation and rate-limiting

The Tumblr API is rate-limited to 1000 requests per hour and 5000 requests per
calendar day (EST). Since the `/posts` endpoint returns at most 20 posts per
requests initialising a large blog can easily take several hours, if not more
than a day. `xapblr index` automatically throttles to respect rate limits.

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
 * `dateparser`
 * `flask` and `flask-assets` (for the web interface)
 * `uwsgi` (for the web interface)
