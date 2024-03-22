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

function submitDateForm() {
    var formData = $("#dateForm").serialize();
    $.post("/set_date", formData, function (response) {
        console.log("Form submitted successfully");
        $('#startDateInput').val(response.start_date);
        $('#endDateInput').val(response.end_date);
    });
    return false;
}

$(document).ready(function () {
    fetchSemesterListItems();
    fetchModuleListItems();
    $("#semesterItemForm").submit(submitSemesterForm);
    $("#moduleItemForm").submit(submitModuleForm);
    $("#dateForm").submit(submitDateForm);
    $("#dateForm").on('reset', function() {
        $.post("/reset_date", function(response) {
            console.log("Date reset successfully");
            $('#startDateInput').val(response.start_date);
            $('#endDateInput').val(response.end_date);
        });
    });
   

    $.get("/get_date", function(data) {
        $('#startDateInput').val(data.start_date);
        $('#endDateInput').val(data.end_date);
    });
});
