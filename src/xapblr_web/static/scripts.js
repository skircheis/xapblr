function getHTML(url, callback) {
    if (!window.XMLHttpRequest) return;

    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
        callback(this.responseText);
    }

    xhr.open('GET', url);
    xhr.responseType = 'text';
    xhr.send();
}

function search(event) {
    event.preventDefault();
    const formData = new FormData(event.target)
    const data = Object.fromEntries(formData.entries());
    fetch("/search",
        {method: "POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }
    ).then( res => res.json()).then(
        res => {
            display_results(res["results"]);
            display_meta(res["meta"]);
        }
    )
}

function display_meta(meta) {
    target = document.querySelector("#results-meta");
    target.style.display = 'block'
    target.querySelector(".count").innerHTML = meta["count"]
    target.querySelector(".time").innerHTML = Math.round(meta["time_ns"] / 1e6);
}

function display_results(results) {
    target = document.querySelector("#results");
    while (target.hasChildNodes()) {
          target.removeChild(target.firstChild);
    }
    results.forEach( res => {
        template = document.querySelector("#templates .result").cloneNode(true);
        body = template.querySelector(".result-body")
        body.innerHTML = res["rendered"];
        tags = template.querySelector(".result-tags")
        res["tags"].forEach( tag => {
            tag_template = document.querySelector("#templates .tag").cloneNode();
            tag_template.innerHTML = "#" + tag;
            tag_template.href = "https://tumblr.com/blog/view/" + res["blog_name"] + "/tagged/" + tag;
            tags.appendChild(tag_template);
        });
        template.querySelector(".toggle").addEventListener("click", toggle_preview)
        external_link = template.querySelector(".external-go a");
        external_link.href = res["post_url"];
        target.appendChild(template);
    }
    );
}

function toggle_preview(event) {
    target = event.target;
    while (!target.classList.contains("result")) {
        target = target.parentNode;
    }
    target = target.querySelector(".result-body");
    if (target.style.overflow == "hidden" ) {
        target.style.overflow = null;
        target.style.maxHeight = null;
    } else if (target.style.overflow == "" ) {
        target.style.overflow = "hidden";
        target.style.maxHeight = "100px";
    }
}
