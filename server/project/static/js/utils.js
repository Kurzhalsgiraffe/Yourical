function copyLink(event) {
    event.preventDefault();

    var link = event.target.href;
    navigator.clipboard.writeText(link);
    alert("Link copied to clipboard: " + link);
}