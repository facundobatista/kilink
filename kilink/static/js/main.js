var linkode = (function (){

    /**
    * Init the module
    * @param {Dict} opts
    */
    function init(opts){
        time_stamp = opts.time_stamp;
        node_list = opts.node_list;
        text_datetime = opts.text_datetime;
        text_tooltip = opts.text_tooltip;


        if (node_list !== false) {
            create_tree();
            $.each($(".node"), function() {
                $(this).tooltipster({
                    trigger: 'hover',
                    content: text_tooltip + $(this).text(),
                });
            });
        }

        $("#timestamp").text(parseDate(time_stamp));
    }

    /**
    * Parse the date
    * @param string date_text
    */
    function parseDate(date_text){
        var timestamp = Date.parse(date_text);
        if(! isNaN(timestamp)){
            return text_datetime + new Date(timestamp).toString();
        }
        return "";
    }


    /**
    * Generate the Tree Node
    */
    function create_tree(){
        var tree_size = {};
        var layout_size = {};
        tree_size.width = 200;
        tree_size.height = 200;
        layout_size.width = 200;
        layout_size.height = 400;

        var tree = d3.layout.tree()
            .sort(null)
            .size([tree_size.width, tree_size.height])
            .children(function(d){
                return (!d.contents || d.contents.length === 0) ? null : d.contents;
            });

        var nodes = tree.nodes(node_list);
        var links = tree.links(nodes);


        var layoutRoot = d3.select(".klk-tree")
            .append("svg:svg").attr("width", layout_size.width).attr("height", layout_size.height)
            .append("svg:g")
            .attr("class", "container")
            .attr("transform", "translate(0,0)");


        // Edges between nodes as a <path class="link" />
        var link = d3.svg.diagonal()
            .projection(function(d){
                var dy = d.y + 40
                return [d.x, dy];
            });

        layoutRoot.selectAll("path.link")
            .data(links)
            .enter()
            .append("svg:path")
            .attr("class", "link")
            .attr("d", link);


        var nodeGroup = layoutRoot.selectAll("g.node")
            .data(nodes)
            .enter()
            .append("svg:g")
            .attr("class", "node")
            .attr("transform", function(d){
                var dy = d.y + 40;
                return "translate(" + d.x + "," + dy + ")";
            });

        nodeGroup.append("svg:circle")
            .attr("class", "node-dot")
            .attr("r", 15)
            .style("fill", function(d){
                if (d.selected) {
                   return "#222222";}
                else {
                   return "#AAAAAA";
                }

            });

        nodeGroup.append("svg:text")
            .attr("text-anchor", "middle")
            .attr("class", "node-text")
            .attr("dy", 5)
            .text(function(d){
                return d.order;
            })
            .on("click", function(node){
                if (!node.selected){
                    window.location = node.url;
                };
            });

        nodeGroup.selectAll(".node-dot")
            .on("click", function(node){
                if (!node.selected){
                    select_node(node);
                };
        });
    }

    /**
    * Redirect to selected kilink
    * In the future, can load the kilink without redirect
    * @param node node
    */
    function select_node(node){
        window.location = node.url;
    }


    // values
    var time_stamp;
    var node_list;
    var text_datetime;
    var text_tooltip;


    var module = {
        init: init,
    }

    return module;

}())


var editor = (function (){

    /**
    * Init the module
    * @param {Dict} opts
    */
    function init(opts){

        $editor = CodeMirror.fromTextArea(document.getElementById("code"), {
            theme: 'monokai',
            lineNumbers: true,
            tabMode: "indent",
            autofocus: true,
            viewportMargin: Infinity,
            extraKeys: {
                "F11": function(cm) {
                    cm.setOption("fullScreen", true)
                },
                "Esc": function(cm) {
                     cm.setOption("fullScreen", false)
                },
                "Ctrl-Enter": function(cm){
                    $("#pasteform").submit();
                }
            }
        });

        $modeInput = document.getElementById("selectlang");

        var backInput = document.getElementById("text_type");
        var bmode = backInput.value;
        if (bmode in {'':0, 'auto':0}){
            autoDetection = 1;
            update();
        }
        else{
            autoDetection = 0;
            $modeInput.value = bmode;
            $editor.setOption("mode", langLike(bmode));
            isPython(bmode);
        }
        
        $editor.on("change", function() {
            if (autoDetection){
                setTimeout(update, 400);
            }
        });
    }

    function selectMode() {
        var mode = $modeInput.options[$modeInput.selectedIndex].innerHTML;
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
            $editor.setOption("mode", cmode);
            isPython(cmode);
            $modeInput.options[0].text = "auto";
        }
    }

    function looksLike(contents) {
        var info = hljs.highlightAuto(contents.trim());
        var clang = langLike(info.language)
        return clang;
    }

    function langLike(lang){
        if (lang in {'cpp':0, 'c++':0, 'cs':0, 'c#':0, 'c':0, 'scala':0, 'java':0}){
            ang = "clike";
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
        else if (lang in languages){
            
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
        var langMode = looksLike($editor.getValue());
        $editor.setOption("mode", langMode);
        isPython(langMode);
        $modeInput.options[$modeInput.selectedIndex].text = "auto: " + capitalise(langMode);
    }

    function capitalise(string){
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    function isPython(imode){
        if (imode == "python"){
            $editor.setOption("indentUnit", 4);
        }
        else{
            $editor.setOption("indentUnit", 2);
        }
    }

    var $editor;
    var $modeInput

    // var pending;
    var autoDetection = 1;
    var languages =  {'1c':0, 'avr':0, 'assembler':0, 'actionscript':0,
            'apache':0, 'applescript':0, 'axapta':0, 'bash':0, 'brainfuck':0,
            'cmake':0, 'dos':0, '.bat':0, 'delphi':0, 'django':0, 'glsl':0,
            'ini':0, 'lisp':0, 'mel':0, 'matlab':0, 'nginx':0, 'objectivec':0,
            'parser3':0, 'profile':0, 'rsl':0, 'rib':0, 'vhdl':0, 'vala':0}

    var module = {
        init: init,
        selectMode: selectMode,
    }

    return module;
}())
