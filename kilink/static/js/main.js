$(document).ready(function(){
    jQuery('textarea').bind('keydown', 'ctrl+return', function(e) {
        $('#pasteform').submit();
    });
});