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
        close_tree_img = opts.close_tree_img;
        open_tree_img = opts.open_tree_img;
        open_tree_tooltip = opts.open_tree_tooltip
        closed_tree_tooltip = opts.closed_tree_tooltip

        $("#toogle-image").tooltipster({
            trigger: 'hover',
            side: 'left'
        })

        if (node_list !== false) {
            create_tree();
            $.each($(".node"), function() {
                $(this).tooltipster({
                    trigger: 'hover',
                    content: text_tooltip + $(this).text(),
                });
            });

            $("#tree-toggle-panel").show();
            $("#toggle-container").on("click", toggleTree)

            // Only if nodes >= 2 
            if(node_list["children"]){
                toggleTree();
            }
        }

        $("#timestamp").text(parseDate(time_stamp));

    }

    /**
    * Toggle the tree panel
    */
    function toggleTree(){
        var cp = $(".code-panel");
        var tp =$(".tree-panel");
        if(cp.hasClass("col-md-12")){
            // Tree is closed
            cp.removeClass("col-md-12").addClass("col-md-10");
            tp.show();
            $("#toogle-image").attr("src", close_tree_img)
            $("#toogle-image").tooltipster("content", closed_tree_tooltip);
            //Now is open
        }
        else{
            //Tree is open
            cp.removeClass("col-md-10").addClass("col-md-12");
            tp.hide();
            $("#toogle-image").attr("src", open_tree_img)
            $("#toogle-image").tooltipster("content", open_tree_tooltip)
            //Now is closed
        }
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
            .append("svg:svg")
            .attr("width", layout_size.width)
            .attr("height", layout_size.height)
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
    var close_tree_img;
    var open_tree_img;
    var open_tree_tooltip;
    var closed_tree_tooltip;


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

        
    }

    /**
    * Late Init for the mode
    */
    function init_mode(){
        $modeInput = $("#selectlang");
        $backInput = $("#text_type");

        var bmode = $backInput.val();
        if ($.inArray(bmode, ['', 'auto']) >=0 ){
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

    /**
    * Set the mode selected in the ddl
    */
    function selectMode() {
        var mode = $modeInput.find("option:selected").val();
        var cmode = langLike(mode.toLowerCase());
        if (cmode == "auto"){
            autoDetection = 1;
            update();
        }
        else{
            autoDetection = 0;
            $editor.setOption("mode", cmode);
            isPython(cmode);
            $modeInput.find("option:first").text("auto");
        }
    }


    /**
    * Get an estimate of the language based on the content
    * @param string content
    */
    function looksLike(contents) {
        var info = hljs.highlightAuto(contents.trim());
        var clang = langLike(info.language)
        return clang;
    }

    /**
    * Get the mode based on the language
    * @param string lang
    */
    function langLike(lang){
        if ($.inArray(lang, c_languages) >= 0){
            lang = "clike";
        }
        else if (lang == "bash"){
            lang = "shell";
        }
        else if (lang == "html"){
            lang = "xml";
        }
            else if (lang == "json"){
        lang = "javascript";
        }
            else if (lang == "tex"){
        lang = "stex";
        }
        else if ($.inArray(lang, plain_languages) >= 0){
            lang = "plain text";
        }
        else if (typeof lang === "undefined"){
            lang = "plain text";
            // "plain text" does not exist,
            // it is a dummy mode to get easily "plain text" mode
        }
        else {
            //do nothing
        }

        return lang;
    }

    /**
    * Update the mode when language is auto
    */
    function update() {
        var langMode = looksLike($editor.getValue());
        $editor.setOption("mode", langMode);
        isPython(langMode);
        $modeInput.find("option:selected").text("auto: " + capitalise(langMode));
    }


    /**
    * Capitalise the text
    * @param string string
    */
    function capitalise(string){
        return string.charAt(0).toUpperCase() + string.slice(1);
    }


    /**
    * Set indent to 4 if python, else 2
    * @param string mode
    */
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
    var $backInput

    var autoDetection = 1;
    var plain_languages =  ['1c', 'avr', 'assembler', 'actionscript',
                            'apache', 'applescript', 'axapta', 'bash', 'brainfuck',
                            'cmake', 'dos', '.bat', 'delphi', 'django', 'glsl',
                            'ini', 'lisp', 'mel', 'matlab', 'nginx', 'objectivec',
                            'parser3', 'profile', 'rsl', 'rib', 'vhdl', 'vala'];
    var c_languages = ['cpp', 'c++', 'cs', 'c#', 'c', 'scala', 'java'];
    var module = {
        init: init,
        init_mode: init_mode,
        selectMode: selectMode,
    }

    return module;
}())
