// Function to fetch list items from the server
function fetchListItems() {
    $.get("/list", function (data) {
        var itemList = $("#itemList");
        itemList.empty(); // Clear the list
        data.forEach(function (item) {
            itemList.append('<li><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"><label for="' + item.id + '">' + item.name + '</label></li>');
        });
    });
}

function submitForm() {
    var formData = $("#itemForm").serialize();
    $.post("/process_selection", formData, function (response) {
        console.log("Form submitted successfully");
    });
    return false;
}

$(document).ready(function () {
    fetchListItems();
    $("#itemForm").submit(submitForm);
});
