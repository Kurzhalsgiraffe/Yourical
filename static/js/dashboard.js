// Function to fetch list items from the server
function fetchListItems() {
    $.get("/list", function (data) {
        var itemList = $("#itemList");
        itemList.empty(); // Clear the list
        // Append each item to the list
        data.forEach(function (item) {
            itemList.append('<li><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.id + '"><label for="' + item.id + '">' + item.name + '</label></li>');
        });
    });
}

// Call the function to fetch list items when the page loads
$(document).ready(function () {
    fetchListItems();
});
