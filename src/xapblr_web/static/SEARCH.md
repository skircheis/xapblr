Search terms
============

`xapblr`'s search terms generally match those of `notmuch`. If you know how
to work with `notmuch`, you already know most of `xapblr`.

The boolean operators `OR` and `AND`, `NOT`, and parentheses `()` can be used to combine multiple predicates.
The default connective is `AND`.

## Predicates

* `<word-or-quoted-phrase>`
    Match terms in the bodies of posts.
    Image alt texts are also indexed.
* `op:<blog-name>`
    Match posts where the root post is from `<blog-name>`.
* `author:<blog-name>`
    Match posts where any post in the reblog chain is from `<blog-name>`.
* `tag:<tag>`
    Match posts tagged `#<tag>`
* `date:<since>..<until> or date:<date>` (NYI)
    Match posts made between `<since>` and `<until>`

    `xapblr` aims to support the same date and time search as `notmuch`; see the [`notmuch` documentation](https://notmuchmail.org/doc/latest/man7/notmuch-search-terms.html#date-and-time-search) for details.
* `link:<domain>`
    Match posts that link to `<domain>` or any of its subdomains. E.g.,
    `link:wikipedia.org` matches both posts with links to `en.wikipedia.org`
    and `jp.wikipedia.org.`

## Caveats

Tags that contain spaces and other special characters *must* be enclosed in
literal double quotes. Thus, to search for posts tagged `#install gentoo`, you
must pass `tag:"install gentoo"`. On the command line, further enclosing the
whole term in *single* quotes is necessary to protect the double quotes from
the shell.
