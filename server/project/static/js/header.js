$(document).ready(function () {
    $(document).ready(function () {
        var burger = $('#id_burger');

        burger.click(function() {
            var navbar = $('#id_navbar');
            navbar.toggle(); // Toggle between display block and none
        });
    });
});