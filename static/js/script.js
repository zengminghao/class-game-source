function disableLinks() {
    var elements = document.getElementsByTagName("a");
    for (var i = 0, len = elements.length; i < len; i++) {
        elements[i].onclick = function() {
            return false;
        };
    }
};

$(".alert").delay(4000).slideUp(200, function() {
    $(this).alert('close');
});

$('.confirmation').on('click', function () {
    return confirm('Are you sure?');
});

