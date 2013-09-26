function isFullScreen(cm) {
  return /\bCodeMirror-fullscreen\b/.test(cm.getWrapperElement().className);
}
function winHeight() {
  return window.innerHeight || (document.documentElement || document.body).clientHeight;
}
function setFullScreen(cm, full) {
  var wrap = cm.getWrapperElement();
  if (full) {
    wrap.className += " CodeMirror-fullscreen";
    wrap.style.height = winHeight() + "px";
    document.documentElement.style.overflow = "hidden";
  } else {
    wrap.className = wrap.className.replace(" CodeMirror-fullscreen", "");
    wrap.style.height = "";
    document.documentElement.style.overflow = "";
  }
  cm.refresh();
}

CodeMirror.on(window, "resize", function() {
  var showing = document.body.getElementsByClassName("CodeMirror-fullscreen")[0];
  if (!showing) return;
  showing.CodeMirror.getWrapperElement().style.height = winHeight() + "px";
});

var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
  lineNumbers: true,
  tabMode: "indent",
  autofocus: true,
  extraKeys: {
        "F11": function(cm) {
          setFullScreen(cm, !isFullScreen(cm));
        },
        "Esc": function(cm) {
          if (isFullScreen(cm)) setFullScreen(cm, false);
        }
  }
});

editor.setOption("theme", 'monokai');

/* Run update function first to highlight pre-existent code */

window.onload = function () {
  setTimeout(function () {
    var backInput = document.getElementById("text_type");
    var bmode = backInput.value;
    if (bmode in {'':0, 'auto':0}){
    autoDetection = 1;
    update();
    }
    else{
    autoDetection = 0;
    modeInput.value = bmode;
    editor.setOption("mode", bmode);
    }
  },1)
}

/* Mode (language) selector */

var modeInput = document.getElementById("seleclang");
function selectMode() {
  var mode = modeInput.options[modeInput.selectedIndex].innerHTML;
  forkMode(mode);
}

function forkMode(inmode) {
  var cmode = langLike(inmode.toLowerCase());
  if (cmode=="auto"){
    autoDetection = 1;
    update();
  }
  else{
    autoDetection = 0;
    editor.setOption("mode", cmode);
    modeInput.options[0].text = "auto";
  }
}

/* Autodetector */

var autoDetection = 1;
editor.on("change", function() {
  if (autoDetection){
    clearTimeout(pending);
    setTimeout(update, 400);
  }
  else{
    //do nothing
  }
});

var pending;
function looksLike(contents) {
  var info = hljs.highlightAuto(contents.trim());
  var clang = langLike(info.language)
  return clang;
}

function langLike(lang) {
  if (lang in {'cpp':0, 'c++':0, 'cs':0, 'c#':0, 'c':0, 'scala':0, 'java':0}){
    lang = "clike";
  }
  else if (lang=="bash"){
  lang = "shell";
  }
  else if (lang=="html"){
  lang = "xml";
  }
  else if (lang=="json"){
  lang = "javascript";
  }
  else if (lang=="tex"){
  lang = "stex";
  }
  else if (lang in {'1c':0, 'avr':0, 'assembler':0, 'actionscript':0,
        'apache':0, 'applescript':0, 'axapta':0, 'bash':0, 'brainfuck':0,
        'cmake':0, 'dos':0, '.bat':0, 'delphi':0, 'django':0, 'glsl':0,
        'ini':0, 'lisp':0, 'mel':0, 'matlab':0, 'nginx':0, 'objectivec':0,
        'parser3':0, 'profile':0, 'rsl':0, 'rib':0, 'vhdl':0, 'vala':0}){
  lang = "plain text";
  }
  else if (typeof lang === "undefined"){
  lang = "plain text";
  // "plain text" does not exist,
  // it is a dummy mode to get easily "plain text" mode
  }
  else{
    //do nothing
  }
  return lang;
}

function update() {
  var langMode = looksLike(editor.getValue());
  editor.setOption("mode", langMode);
  modeInput.options[modeInput.selectedIndex].text = "auto: " + capitalise(langMode);
}

function capitalise(string)
{
    return string.charAt(0).toUpperCase() + string.slice(1);
}
