function highlightLoadHeur() { 
$(document).ready(function() {
  $('pre').each(function(i, e) {hljs.highlightBlock(e)});
});
}

highlightLoadHeur();