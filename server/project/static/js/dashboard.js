window.addEventListener('scroll', null, { passive: true });

function fetchSemesterListItems() {
    $.get("/get_semester_list", function (data) {
        updateSemesterListItems(data);
    });
}

function updateSemesterListItems(data) {
    var semesterItemTable = $("#semesterItemTable");
    semesterItemTable.empty();

    var containerWidth = semesterItemTable.width();
    var numColumns = Math.floor(containerWidth / 200); // Assuming each column width is 200px, adjust as needed

    var currentRow;
    data.forEach(function (item, index) {
        if (index % numColumns === 0) {
            currentRow = $('<tr></tr>');
            semesterItemTable.append(currentRow);
        }

        var checkbox = $('<input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '">');
        checkbox.prop('checked', item.selected); // Restore original selection
        var label = $('<label for="' + item.id + '">' + item.name + '</label>');
        currentRow.append($('<td></td>').append(checkbox).append(label));
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
    });
}

function updateModuleListItems(data) {
    var moduleItemTable = $("#moduleItemTable");
    moduleItemTable.empty();

    var containerWidth = moduleItemTable.width();
    var numColumns = Math.floor(containerWidth / 275); // Assuming each column width is 275px, adjust as needed

    var currentRow;
    data.forEach(function (item, index) {
        if (index % numColumns === 0) {
            currentRow = $('<tr></tr>');
            moduleItemTable.append(currentRow);
        }

        var checkbox = $('<input type="checkbox" id="' + item.id + '" name="selected_items" value="' + item.name + '">');
        checkbox.prop('checked', item.selected); // Restore original selection
        var label = $('<label for="' + item.id + '">' + item.name + '</label>');
        currentRow.append($('<td></td>').append(checkbox).append(label));
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
});
