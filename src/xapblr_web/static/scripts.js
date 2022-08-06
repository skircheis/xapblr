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
