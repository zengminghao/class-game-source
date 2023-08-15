$("#aliastoggle").click(function(){
    $('.name').toggle();
    $('.alias').toggle();
    if ($(this).text() == "show name") { 
        $(this).text("show alias"); 
    } else { 
        $(this).text("show name"); 
    }; 
});

