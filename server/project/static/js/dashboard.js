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

$("#semesterSearchInput").on("input", function() {
    var searchTerm = $("#semesterSearchInput").val().trim().toLowerCase();
    $('#semesterItemTable input[type="checkbox"]').each(function() {
        var checkbox = $(this);
        if (checkbox.val().toLowerCase().includes(searchTerm)) {
            checkbox.parent().show();
        } else {
            checkbox.parent().hide();
        }
    });
});

$("#semesterItemForm").submit(function (event) {
    event.preventDefault();
    var formData = $("#semesterItemForm").serialize();
    $.post("/submit_semester_selection", formData, function (response) {
        $("#semesterItemFormAlert").removeClass("alert-danger").addClass("alert-success");
        $("#semesterItemFormAlert").text("Semester selection saved");
        fetchModuleListItems();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        $("#semesterItemFormAlert").removeClass("alert-success").addClass("alert-danger");
        $("#semesterItemFormAlert").text(errorMessage);
        console.log("Error: " + errorMessage);
    });
    $("#semesterItemFormAlert").fadeIn().delay(2000).fadeOut();
    return false;
});

$("#resetSemesterButton").click(function () {
    document.getElementById("semesterItemForm").reset();
    $.post("/reset_semester_selection", function (response) {
        $("#semesterItemFormAlert").removeClass("alert-danger").addClass("alert-success");
        $("#semesterItemFormAlert").text("Semester selection reset");
        fetchModuleListItems();
        load_ical_events();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        $("#semesterItemFormAlert").removeClass("alert-success").addClass("alert-danger");
        $("#semesterItemFormAlert").text(errorMessage);
        console.log("Error: " + errorMessage);
    });
    $("#semesterItemFormAlert").fadeIn().delay(2000).fadeOut();
});

function fetchModuleListItems() {
    $.get("/get_module_list", function (data) {
        updateModuleListItems(data);
    });
}

function updateModuleListItems(data) {
    var moduleItemTable = $("#moduleItemTable");
    moduleItemTable.empty();

    var containerWidth = moduleItemTable.width();
    var numColumns = Math.max(Math.floor(containerWidth / 400), 1); // Assuming each column width is 400px, adjust as needed

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

$("#moduleSearchInput").on("input", function() {
    var searchTerm = $("#moduleSearchInput").val().trim().toLowerCase();
    $('#moduleItemTable input[type="checkbox"]').each(function() {
        var checkbox = $(this);
        if (checkbox.val().toLowerCase().includes(searchTerm)) {
            checkbox.parent().show();
        } else {
            checkbox.parent().hide();
        }
    });
});

$("#moduleItemForm").submit(function (event) {
    event.preventDefault();
    var formData = $("#moduleItemForm").serialize();
    $.post("/submit_module_selection", formData, function (response) {
        $("#moduleItemFormAlert").removeClass("alert-danger").addClass("alert-success");
        $("#moduleItemFormAlert").text("Modules saved, calendar created");
        load_ical_events();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        $("#moduleItemFormAlert").removeClass("alert-success").addClass("alert-danger");
        $("#moduleItemFormAlert").text(errorMessage);
        console.log("Error: " + errorMessage);
    });
    $("#moduleItemFormAlert").fadeIn().delay(2000).fadeOut();
    return false;
});

$("#resetModuleButton").click(function () {
    document.getElementById("moduleItemForm").reset();
    $.post("/reset_module_selection", function (response) {
        $("#moduleItemFormAlert").removeClass("alert-danger").addClass("alert-success");
        $("#moduleItemFormAlert").text("Modules reset, calendar reset");
        load_ical_events();
    }).fail(function(xhr, status, error) {
        var errorMessage = JSON.parse(xhr.responseText).message;
        $("#moduleItemFormAlert").removeClass("alert-success").addClass("alert-danger");
        $("#moduleItemFormAlert").text(errorMessage);
        console.log("Error: " + errorMessage);
    });
    $("#moduleItemFormAlert").fadeIn().delay(2000).fadeOut();
});

$(document).ready(function () {
    fetchSemesterListItems();
    fetchModuleListItems();
});
