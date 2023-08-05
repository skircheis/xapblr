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

function fetch_json(url, data) {
    return fetch(url,
        {method: "POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }
    ).then( res => res.json() );
}

// Login view

function login_handler(event) {
    event.preventDefault();
    form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    fetch_json("/login", data).then( res => {
        var target = document.querySelector("#login-message");
        target.innerHTML = res["message"]
        if(res["success"]) {
            target.className = "success";
            window.location.href = "/search";
        } else {
            target.className = "failure";
        }
    }
   );
}

// Search view

function search_handler(event){
    event.preventDefault();
    event.target.querySelector("#page").value = 1;
    search(event.target);
}


function search(form, push_state = true) {
    const formData = new FormData(form)
    const data = Object.fromEntries(formData.entries());
    cached_search = formData;
    if (push_state) {
        var url = "/search/" + formData.get("blog") + "/" + formData.get("query")
        if ( formData.get("page") > 1 ) {
            url += "/page/" + formData.get("page")
        }
        history.pushState(formData, "", url);
    }
    fetch_json("/search", data).then(
        res => {
            display_results(res["results"]);
            display_meta(res["meta"]);
        }
    ).then( res => {
        var target = document.querySelector("#grid");
        target.scrollTop = 0;
        }
    )
}

function set_search_form(form, formData, page) {
    var blog = form.querySelector("#blogurl");
    var query = form.querySelector("#query");
    blog.value = formData.get("blog");
    query.value = formData.get("query");
    if (page) {
        var pager = form.querySelector("#page");
        pager.value = formData.get("page");
    }
}

function paginate(form) {
    set_search_form(form, cached_search, false);
    search(form);
}

function display_meta(meta) {
    var target = document.querySelector("#results-meta");
    var error_disp = document.querySelector("#error");
    var pager = target.querySelector("#page");
    var pages = Math.ceil(meta["matches"]/meta["pagesize"]);
    var paginated = target.querySelector("#results-meta-paginated");
    var complete  = target.querySelector("#results-meta-complete");
    var set_time =  (container) => {
        container.querySelector(".time").innerHTML = Math.round(meta["time_ns"] / 1e6);
    } ;
    if ( meta["error"] != undefined ) {
        target.style.display = "none";
        error_disp.style.display = "block";
        error_disp.querySelector(".error-msg").innerHTML = meta["error"];
        return;
    } else {
        target.style.display = "block";
        error_disp.style.display = "none";
    }
    if ( meta["offset"] > meta["matches"] ) {
        var search_form = document.querySelector("#search-form");
        pager.value = pages;
        paginate(search_form);
    } else if (meta["count"] < meta["matches"] ){
        paginated.style.display = "block";
        complete.style.display = "none";
        target.querySelector(".match_start").innerHTML = meta["offset"] + 1;
        target.querySelector(".match_end").innerHTML = meta["offset"] + meta["count"];
        target.querySelector(".matches_total").innerHTML = meta["matches"];
        set_time(paginated);
    } else {
        complete.style.display = "block";
        paginated.style.display = "none";
        target.querySelector(".count").innerHTML = meta["count"];
        set_time(complete);
    }
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
