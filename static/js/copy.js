// copy button for ics
function copy(myurl) {
  selection = document.getElementById(myurl).innerText;
  navigator.clipboard.writeText(selection).then(function() {
    /* clipboard successfully set */
  }, function() {
    /* clipboard write failed */
  });
}

