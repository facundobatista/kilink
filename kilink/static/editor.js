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
  return info.language;
}

function update() {
  editor.setOption("mode", looksLike(editor.getValue()));
}