// Function to fetch list items from the server
function fetchListItems() {
    $.get("/list", function (data) {
        var itemTable = $("#itemTable");
        itemTable.empty(); // Clear the table

        var currentRow;
        // Append each item to the table with 10 columns
        data.forEach(function (item, index) {
            if (index % 10 === 0) {
                currentRow = $('<tr></tr>');
                itemTable.append(currentRow);
            }
            currentRow.append('<td><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"><label for="' + item.id + '">' + item.name + '</label></td>');
        });
    });
}

function submitForm() {
    // Serialize form data
    var formData = $("#itemForm").serialize();

    // Make AJAX request to process_selection route
    $.post("/process_selection", formData, function (response) {
        // Handle response here if needed
        console.log("Form submitted successfully");
    });

    // Prevent default form submission
    return false;
}

$(document).ready(function () {
    fetchListItems();
    $("#itemForm").submit(submitForm);
});
