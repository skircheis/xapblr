import dateparser

def parse_date(date_str):
    # takes a human-readable datetime string as understood by notmuch and
    # returns a unix timestamp
    # Example inputs:
    # yesterday, 2 hours ago, last wednesday, 5 days ago, 1659706622
    #
    # note (nost) - dateparser works for most of the above but not "last wednesday"
    # but it's quick and easy
    dt = dateparser.parse(date_str)
    if dt is not None:
        return int(dt.timestamp())
    else:
        raise ValueError(f"failed to parse date string: {date_str}")

