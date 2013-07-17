var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
  lineNumbers: true,
  tabMode: "indent"
});

editor.setOption("theme", 'monokai');

editor.on("change", function() {
  clearTimeout(pending);
  setTimeout(update, 400);
});

var pending;
function looksLike(contents) {
  info = hljs.highlightAuto(contents);
  lang = info.language;
  if (lang in {'cpp':0, 'cs':0, 'scala':0, 'java':0})
    {
  lang = "clike";
    }
  else if (lang=="html")
    {
  lang = "xml";
    }
  else if (lang=="json")
    {
  lang = "javascript";
    }        
  else if (lang=="tex")
    {
  lang = "stex";
    }       
  else
    {
//  do nothing    
    }
  return lang;
}

function update() {
  editor.setOption("mode", looksLike(editor.getValue()));
}