from json import dumps
from requests import get
from textwrap import wrap

from .utils import get_author, format_timestamp


def render_json(post, args):
    return dumps(post)


def render_plain(post, args):
    width = args.width or 80
    rendered = [render_plain_one(p, width) for p in post["trail"]]
    rendered.append(render_plain_one(post, width))
    delim = "\n\n" + "=" * width + "\n"
    return ("\n" + "-" * width + "\n").join([r for r in rendered if r]) + delim


def render_plain_poll(block):
    out = f"[Poll] {block['question']}\n"
    out += "\n".join(["* " + a["answer_text"] for a in block["answers"]])
    return out


def render_plain_one(post, width):
    if len(post["content"]) == 0:
        return ""
    user = get_author(post)
    out = f"{user}:\n"
    texts = []
    for block in post["content"]:
        if block["type"] == "text":
            texts.append("\n".join(wrap(block["text"], width=width)))
        elif block["type"] == "poll":
            texts.append(render_plain_poll(block))
        elif block["type"] == "image":
            texts.append("[image]")
    out += "\n\n".join(texts)
    return out


def render_md(post, args):
    width = args.width or 540
    rendered = [render_md_one(p, width) for p in post["trail"]]
    rendered.append(render_md_one(post, width))
    delim = "\n" + "---" + "\n"
    return "\n\n".join([r for r in rendered if r]) + delim


def render_md_one(post, width):
    if len(post["content"]) == 0:
        return ""
    user = get_author(post)
    out = f"**{user}:**\n\n"
    out += "".join(
        [render_md_block(block, width) + "\n\n" for block in post["content"]]
    )
    return out


def render_md_poll(block):
    out = f"**{block['question']}**\n"
    out += "\n".join(["* " + a["answer_text"] for a in block["answers"]])
    return out


def render_md_block(block, pref_width):
    if block["type"] == "text":
        return block["text"] + "\n"
    if block["type"] == "poll":
        return render_md_poll(block) + "\n"
    elif block["type"] == "image":
        disp_width = 0
        orig_url = None
        for m in block["media"]:
            if m.get("has_original_dimensions", False):
                orig_url = m["url"]
            w = m["width"]
            if abs(pref_width - w) < abs(pref_width - disp_width):
                disp_width = w
                disp_url = m["url"]
        if orig_url:
            return f"[![]({disp_url})]({orig_url})"
        else:
            return f"![]({disp_url})"

    return ""


def render_html(post, args):
    rendered = [render_html_one(p) for p in post["trail"]]
    rendered.append(render_html_one(post))
    delim = "\n<hr />\n"
    inner_html = delim.join([r for r in rendered if r])

    from datetime import datetime

    ts = post["timestamp"]
    dt = datetime.fromtimestamp(ts)
    ts_hf = format_timestamp(ts)
    ts_iso = dt.isoformat()
    ts_words = dt.strftime("%B %-d, %Y at %H:%m")
    return (
        "<div class='tumblr-post'>\n\t"
        f'<time datetime="{ts_iso}" title="{ts_words}">{ts_hf}</time>'
        + inner_html.replace("\n", "\n\t")[:-1]
        + "\n</div>\n"
    )


def render_html_one(post):
    if len(post["content"]) == 0:
        return ""
    user = get_author(post)
    out = f'<p class="blog-name">\n\t{user}:\n</p>\n'
    out += "".join(
        ["<p>\n\t" + render_html_block(block) + "\n</p>\n" for block in post["content"]]
    )
    return out


def render_html_poll(block):
    out = f"<span class=\"poll_question\"> {block['question']}</span>\n"
    out += (
        '<ul class="poll_answers">\n'
        + "\n".join([f"<li>{a['answer_text']}</li>" for a in block["answers"]])
        + "</ul>"
    )
    return out


def render_html_block(block):
    if block["type"] == "text":
        return block["text"] + "\n"
    elif block["type"] == "poll":
        return render_html_poll(block)
    elif block["type"] == "image":
        orig_url = None
        sources = []
        for m in block["media"]:
            sources.append(f'{m["url"]} {m["width"]}w')
            if m.get("has_original_dimensions", False):
                orig_url = m["url"]
        srcset = ", ".join(sources)
        imgtag = f'<img srcset="{srcset}" />'
        if orig_url:
            return f'<a href="{orig_url}">{imgtag}</a>'
        else:
            return imgtag

    return ""


def render_embed(post, args):
    url = "https://www.tumblr.com/oembed/1.0"
    response = get(url, {"url": post["post_url"]})
    return response.json()["html"]


renderers = {
    "json": render_json,
    "html": render_html,
    "embed": render_embed,
    "plain": render_plain,
    "md": render_md,
}
