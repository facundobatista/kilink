$(document).ready(function(){
    $('textarea').bind('keydown', 'ctrl+return', function(e) {
        $('#pasteform').submit();
    });

    $(".kilink-timestamp").text(text_timestamp);
});
