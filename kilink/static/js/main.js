$(document).ready(function(){
    jQuery('textarea').bind('keydown', 'ctrl+return', function(e) {
        $('#pasteform').submit();
    });
    // var editor = CodeMirror.fromTextArea("placeholder");
    var editor = $('.CodeMirror')[0].CodeMirror
    jQuery('#wrap').bind('change', function(){
        //console.log($(this).prop("checked"));
        if($(this).prop("checked")){
            editor.setOption('lineWrapping', true)
        }
        else{
            editor.setOption('lineWrapping', false)
        }
    })
});
