$(document).ready(function () {
    var burger = $('#id_burger');
    var navbar = $('#id_navbar');

    burger.click(function() {
        navbar.toggle();
        burger.toggleClass('open');
    });
});
