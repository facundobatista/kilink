var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
//  mode: "python",
  lineNumbers: true,
  tabMode: "indent"
});

editor.setOption("theme", 'monokai');

var tempoc;
editor.on("change", function() {
  clearTimeout(tempoc);
  setTimeout(highlightLoadHeur, 400);
});

/*
  editor.on("change", function() {
    clearTimeout(pending);
    setTimeout(update, 400);
  });

  var pending;
  function looksLikeScheme(code) {
    return !/^\s*\(\s*function\b/.test(code) && /^\s*[;\(]/.test(code);
  }

  function update() {
    editor.setOption("mode", looksLikeScheme(editor.getValue()) ? "scheme" : "javascript");
  }
*/
