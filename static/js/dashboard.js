window.addEventListener('scroll', null, { passive: true });

function fetchSemesterListItems() {
    $.get("/get_semester_list", function (data) {
        updateSemesterListItems(data);

        $(window).resize(function () {
            updateSemesterListItems(data);
        });
    });
}

function updateSemesterListItems(data) {
    var semesterItemTable = $("#semesterItemTable");
    semesterItemTable.empty();

    var containerWidth = semesterItemTable.width();
    var numColumns = Math.floor(containerWidth / 200); // Assuming each column width is 150px, adjust as needed

    var currentRow;
    data.forEach(function (item, index) {
        if (index % numColumns === 0) {
            currentRow = $('<tr></tr>');
            semesterItemTable.append(currentRow);
        }

        var checked = item.selected ? "checked" : "";
        currentRow.append('<td><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"' + checked + '><label for="' + item.id + '">' + item.name + '</label></td>');
    });
}

function submitSemesterForm() {
    var formData = $("#semesterItemForm").serialize();
    $.post("/process_semester_selection", formData, function (response) {
        $("#semesterItemFormAlert").fadeIn().delay(2000).fadeOut();
        fetchModuleListItems();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        console.log("Error: " + errorMessage);
    });
    return false;
}

function fetchModuleListItems() {
    $.get("/get_module_list", function (data) {
        updateModuleListItems(data);

        $(window).resize(function () {
            updateModuleListItems(data);
        });
    });
}

function updateModuleListItems(data) {
    var moduleItemTable = $("#moduleItemTable");
    moduleItemTable.empty();

    var containerWidth = moduleItemTable.width();
    var numColumns = Math.floor(containerWidth / 400); // Assuming each column width is 400px, adjust as needed

    var currentRow;
    data.forEach(function (item, index) {
        if (index % numColumns === 0) {
            currentRow = $('<tr></tr>');
            moduleItemTable.append(currentRow);
        }

        var checked = data[index].selected ? "checked" : "";
        currentRow.append('<td><input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '"' + checked + '><label for="' + item.id + '">' + item.name + '</label></td>');
    });
}

function submitModuleForm() {
    var formData = $("#moduleItemForm").serialize();
    $.post("/process_module_selection", formData, function (response) {
        $("#moduleItemFormAlert").fadeIn().delay(2000).fadeOut();
        load_events();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        console.log("Error: " + errorMessage);
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

function copyLink(event) {
    event.preventDefault();

    var link = event.target.href;
    navigator.clipboard.writeText(link);
    alert("Link copied to clipboard: " + link);
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
