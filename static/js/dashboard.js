function fetchSemesterListItems() {
    $.get("/get_semester_list", function (data) {
        var semesterItemTable = $("#semesterItemTable");
        semesterItemTable.empty();

        var currentRow;
        // Append each item to the table with 12 columns
        data.forEach(function (item, index) {
            if (index % 12 === 0) {
                currentRow = $('<tr></tr>');
                semesterItemTable.append(currentRow);
            }
            currentRow.append('<td><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"><label for="' + item.id + '">' + item.name + '</label></td>');
        });
    });
}

function submitSemesterForm() {
    var formData = $("#semesterItemForm").serialize();
    $.post("/process_semester_selection", formData, function (response) {
        console.log("Form submitted successfully");
        fetchModuleListItems();
    });
    return false;
}

function fetchModuleListItems() {
    $.get("/get_module_list", function (data) {
        var moduleItemTable = $("#moduleItemTable");
        moduleItemTable.empty();

        var currentRow;
        // Append each item to the table with 4 columns
        data.forEach(function (item, index) {
            if (index % 4 === 0) {
                currentRow = $('<tr></tr>');
                moduleItemTable.append(currentRow);
            }
            currentRow.append('<td><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"><label for="' + item.id + '">' + item.name + '</label></td>');
        });
    });
}

function submitModuleForm() {
    var formData = $("#moduleItemForm").serialize();
    $.post("/process_module_selection", formData, function (response) {
        console.log("Form submitted successfully");
    });
    return false;
}

$(document).ready(function () {
    fetchSemesterListItems();
    fetchModuleListItems();
    $("#semesterItemForm").submit(submitSemesterForm);
    $("#moduleItemForm").submit(submitModuleForm);
});
