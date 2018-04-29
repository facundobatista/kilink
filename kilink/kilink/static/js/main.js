var linkode = (function (){
    /**
     * Init the module.
     * @param  {dict}
     */
    function init(opts){
        text_new_submit = opts.text_new_submit;
        text_datetime = opts.text_datetime;
        text_update_submit = opts.text_update_submit;
        text_tooltip = opts.text_tooltip;
        text_success_noty = opts.text_success_noty;
        text_retry_noty = opts.text_retry_noty;
        text_retry_times_noty = opts.text_retry_times_noty;
        text_get_error_noty = opts.text_get_error_noty;
        text_get_not_exist_noty = opts.text_get_not_exist_noty;
        text_post_error_noty = opts.text_post_error_noty;
        text_post_too_big_noty = opts.text_post_too_big_noty;
        text_post_not_exist_noty = opts.text_post_not_exist_noty;
        text_retry_button = opts.text_retry_button;

        close_tree_img = opts.close_tree_img;
        open_tree_img = opts.open_tree_img;
        open_tree_tooltip = opts.open_tree_tooltip;
        closed_tree_tooltip = opts.closed_tree_tooltip;

        current_linkode_id = null;
        first_load_success = true;

        tooltipster_default();
        noty_default();

        if(linkode_id_val()){
            $("#btn-submit").text(text_update_submit);
            api_get(linkode_id_val(), true, true);
        }
        else{
            $("#btn-submit").text(text_new_submit);
        }

        $("#toggle-container").on("click", function(){
            toggleTree();
        });
        $("#btn-submit").on("click", function(){
            api_post();
        });
    }

    /**
     * Get or set the current_linkode_id
     * @param  {string}
     * @return {string}
     */
    function linkode_id_val(new_linkode_id){
        if (new_linkode_id) {
            window.location.hash = new_linkode_id;
            current_linkode_id = new_linkode_id;
        } 
        else {
            if(!current_linkode_id){
                hash = window.location.hash.replace("#", "");
                path = window.location.pathname.split("/").pop();

                if (hash){
                    current_linkode_id = hash;
                }
                else if (path){
                    current_linkode_id = path;
                }
                else{
                    current_linkode_id = null;
                }
            }

            return current_linkode_id;
        }
    }

    /**
     * Post the new linkode
     * @param  {string}
     */
    function api_post(current_retry){
        var api_post_url = API_URL;
        var text_type = $("#selectlang").val().replace("auto_", "");
        var post_data = {
            'content': editor.val(),
            'text_type': text_type
        };

        if(first_load_success && linkode_id_val()){
            api_post_url = api_post_url + linkode_id_val();
            post_data.parent = linkode_id_val();
        }

        $.post(api_post_url,post_data)
            .done(function(data) {
                var posted_linkode = data;
                if(first_load_success){
                    linkode_id_val(posted_linkode.revno);
                    $("#selectlang").val(text_type);
                    editor.selectMode();
                    api_after_post_get(posted_linkode.revno);
                    $("#btn-submit").text(text_update_submit);
                    show_success_noty(posted_linkode.revno);
                }
                else{
                    window.location.replace(URL_BASE + "/#" + posted_linkode.revno);
                }
            })
            .fail(function(data, error) {
                current_retry = current_retry ? current_retry : 0;
                if (current_retry < RETRY_TIMES && data.status != 404 && data.status != 413){
                    retry_delay = RETRY_DELAYS[current_retry];
                    current_retry++;
                    show_retry_noty(retry_delay);
                    setTimeout(function(){
                        api_post(current_retry);
                    }, retry_delay);
                }
                else{
                    show_error_noty(data.status, true, api_post, []);
                }
            });
    }

    /**
     * Create the tree and set timestamp.
     * @param  {string}
     */
    function api_after_post_get(linkode_id){
        var api_get_url = API_URL + linkode_id;
        return $.get(api_get_url)
                .done(function(data) {
                    node_list = data.tree;
                    $("#tree-toggle-panel").show();
                    if (node_list !== false) {
                        $(".klk-tree").empty();
                        create_tree(linkode_id);
                        if(node_list.children){
                            toggleTree(true);
                        }
                    }
                    set_timestamp(data.timestamp);
                });
    }

    /**
     * Get the linkode
     * @param  {string}
     * @param  {bool}
     * @param  {bool}
     * @param  {int}
     */
    function api_get(linkode_id, include_tree, first_load, current_retry) {
        var api_get_url = API_URL + linkode_id;
        result = $.get(api_get_url)
                .done(function(data) {
                    load_linkode(data.content, data.text_type, data.timestamp);
                    if(include_tree){
                        node_list = data.tree;
                        if (node_list !== false) {
                            $(".klk-tree").empty();
                            create_tree(linkode_id);
                            $("#tree-toggle-panel").show();

                            // Only if nodes >= 2 
                            if(node_list.children){
                                toggleTree();
                            }
                        }
                    }
                    else{
                        color_node(linkode_id);
                    }
                    if(!first_load){
                        linkode_id_val(linkode_id);
                    }
                })
                .fail(function(data, error) {
                    if(first_load || data.status == 404){
                        first_load_success = false;
                        $("#btn-submit").text(text_new_submit);
                        show_error_noty(data.status, false, 
                                        api_get, 
                                        [linkode_id, include_tree, first_load, 0]);
                    }
                    else{
                        current_retry = current_retry ? current_retry : 0;
                        if (current_retry < RETRY_TIMES){
                            retry_delay = RETRY_DELAYS[current_retry];
                            current_retry++;
                            show_retry_noty(retry_delay);
                            setTimeout(function(){
                                result = api_get(linkode_id, include_tree, false, current_retry);
                            }, retry_delay);
                        }
                        else{
                            show_error_noty(data.status, false, 
                                            api_get, 
                                            [linkode_id, include_tree, first_load, 0]);
                        }
                    }
                });
        return result;
    }

    /**
     * Set the timestamp of the current linkode
     * @param {string}
     */
    function set_timestamp(date_text){
        var timestamp = Date.parse(date_text);
        if(! isNaN(timestamp)){
            $("#timestamp").text(text_datetime + new Date(timestamp).toString());
        }
        else{
            $("#timestamp").text("");
        }
    }

    /**
     * Load the linkode to the page
     * @param  {string}
     * @param  {string}
     * @param  {string}
     */
    function load_linkode(content, text_type, timestamp){
        //Reset the auto option.
        $("#selectlang option[value^='auto']").text("auto");
        $("#selectlang option[value^='auto']").val("auto");
        $("#selectlang").val(text_type);
        editor.selectMode();
        set_timestamp(timestamp);
        editor.val(content);
    }

    /**
     * @param  {bool}
     * @return {[type]}
     */
    function toggleTree(force_open){
        var cp = $(".code-panel");
        var tp =$(".tree-panel");

        if(cp.hasClass("col-md-12") || force_open){
            // Tree is closed
            cp.removeClass("col-md-12").addClass("col-md-10");
            tp.show();
            $("#toogle-image").attr("src", close_tree_img);
            $("#toogle-image").tooltipster("content", closed_tree_tooltip);
            //Now is open
        }
        else{
            //Tree is open
            cp.removeClass("col-md-10").addClass("col-md-12");
            tp.hide();
            $("#toogle-image").attr("src", open_tree_img);
            $("#toogle-image").tooltipster("content", open_tree_tooltip);
            //Now is closed
        }
    }

    /**
     * Generate the Tree Node
     * @param  {string}
     */
    function create_tree(linkode_id){
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
                var dy = d.y + 40;
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
            .attr("r", 15);

        color_node(linkode_id);

        nodeGroup.append("svg:text")
            .attr("text-anchor", "middle")
            .attr("class", "node-text")
            .attr("dy", 5)
            .text(function(d){
                return d.order;
            })
            .on("click", function(node){
                select_node(node);
            });

        nodeGroup.selectAll(".node-dot")
            .on("click", function(node){
                select_node(node);
            });

        $.each($(".node"), function() {
            $(this).tooltipster({
                trigger: 'hover',
                content: text_tooltip + $(this).text(),
            });
        });
    }

    /**
     * Selected kilink
     * @param  {node}
     */
    function select_node(node){
        if (!node.selected){
            api_get(node.linkode_id, false, false, 0);
        }
    }

    /**
     * Unselect all kilinks
     * @param  {string}
     */
    function color_node(linkode_id) {
        nodeGroup = d3.select(".klk-tree").selectAll("g.node");
        nodeGroup.selectAll(".node-dot")
        .style("fill", function(node){
            if (node.linkode_id == linkode_id) {
                node.selected = true;
                return "#222222";}
            else {
                node.selected = false;
                return "#AAAAAA";
            }

        });
    }

    /**
     * Show the success notification
     * @param  {string}
     */
    function show_success_noty(linkode_id){
        var n = new Noty({
                type: 'success',
                text: text_success_noty + " " + linkode_id,
                timeout: 2000,
                progressBar: false,
                queue: 'q_success',
                killer: true,

            }).show();
    }

    /**
     * Show retry notification
     * @param  {int}
     */
    function show_retry_noty(retry_delay){
        var n = new Noty({
                type: 'info',
                text: text_retry_noty + " " + retry_delay / 1000 + " " + text_retry_times_noty,
                timeout: retry_delay - 500, // subtract 500 ms to avoid overlap
                progressBar: true,
                queue: 'q_rety',
                killer: 'q_rety',
            }).show();
    }

    /**
     * Show error notification
     * @param  {int}
     * @param  {boolean}
     * @param  {function}
     * @param  {params}
     */
    function show_error_noty(error_number, is_post, retry_func, retry_params){
        if (error_number == 404){
            text = is_post ? text_post_not_exist_noty : text_get_not_exist_noty;
            buttons = [];
        }
        else if (error_number == 413){
            text = text_post_too_big_noty;
            buttons = [];
        }
        else {
            text =  is_post ? text_post_error_noty : text_get_error_noty;
            buttons = [
                Noty.button(text_retry_button, 'btn btn-default', function(){
                    n.close();
                    //retry_func(...retry_params); // Spread Operator only ES6
                    retry_func.apply(null,retry_params); // ES5 Spread Operator solution
                })
            ];
        }

        var n = new Noty({
                type: 'error',
                text: text,
                killer: true,
                buttons: buttons,
            }).show();
    }

    /**
     * Set the default values for noty
     */
    function noty_default(){
        Noty.overrideDefaults({
            theme: 'metroui',
            layout: 'topRight',
            timeout: false,
            progressBar: false,
            closeWith: ['button'],
            animation: {
                open: 'noty_effects_open',
                close: 'noty_effects_close'
            },
            id: false,
            force: false,
            killer: false,
            queue: 'global',
            container: false,
            buttons: [],
            sounds: {},
            titleCount: {
                conditions: []
            },
            modal: false
        });
    }

    /**
     * Set the default values for tooltipster
     */
    function tooltipster_default(){
        $("#toogle-image").tooltipster({
            trigger: 'hover',
            side: 'left'
        });
    }

    // constants
    var URL_BASE = window.location.protocol + "//" + window.location.host;
    var API_URL = URL_BASE + "/api/1/linkodes/";
    var RETRY_TIMES = 3;
    var RETRY_DELAYS = [2000, 10000, 30000]; // in miliseconds

    // values
    var text_update_submit;
    var text_new_submit;
    var text_tooltip;
    var text_datetime;
    var text_success_noty;
    var text_retry_noty;
    var text_retry_times_noty;
    var text_get_error_noty;
    var text_get_not_exist_noty;
    var text_post_error_noty;
    var text_post_too_big_noty;
    var text_post_not_exist_noty;
    var text_retry_button;
    
    var close_tree_img;
    var open_tree_img;
    var open_tree_tooltip;
    var closed_tree_tooltip;

    // vars
    var current_linkode_id;
    var first_load_success;

    var module = {
        init : init,
    };

    return module;

}());


var editor = (function (){

    /**
    * Init the module
    * @param {Dict} opts
    */
    function init(opts){
        $modeInput = $("#selectlang");
        $backInput = $("#text_type");

        $editor = CodeMirror.fromTextArea(document.getElementById("code"), {
            theme: 'monokai',
            lineNumbers: true,
            tabMode: "indent",
            autofocus: true,
            viewportMargin: Infinity,
            extraKeys: {
                "F11": function(cm) {
                    cm.setOption("fullScreen", true);
                },
                "Esc": function(cm) {
                     cm.setOption("fullScreen", false);
                },
                "Ctrl-Enter": function(cm){
                    $("#btn-submit").click();
                }
            }
        });

        $editor.on("change", function() {
            if (autoDetection){
                setTimeout(update, 400);
            }
        });
    }

    /**
    * Set the editor mode
    * @param string mode
    */
    function setMode(mode){
        var editor_mode = "";
        if(language_editor_mode[mode]){
            editor_mode = language_editor_mode[mode];
        }
        $editor.setOption("mode", editor_mode);
        needIndent(mode);
    }

    /**
    * Set indent by mode
    * @param string mode
    */
    function needIndent(mode){
        if (mode == "python"){
            $editor.setOption("indentUnit", 4);
        }
        else{
            $editor.setOption("indentUnit", 2);
        }
    }

    /**
    * Set the mode selected in the ddl
    */
    function selectMode() {
        var mode = $modeInput.find("option:selected").val();
        if (mode == "auto" || mode.startsWith("auto_")){
            autoDetection = 1;
            update();
        }
        else{
            autoDetection = 0;
            setMode(mode);
            setAutoOption("auto", "auto");
        }
    }

    /**
    * Get or set the text in the editor
    */
    function val(new_val){
        if (new_val){   
            $editor.setValue(new_val);
        }
        else {
            return $editor.getValue();
        }
    }


    /**
    * Get an estimate of the language based on the content
    * @param string content
    */
    function looksLike(contents) {
        var info = hljs.highlightAuto(contents.trim());
        if(auto_language[info.language]){
            return auto_language[info.language];
        }
        return "plain text";
    }

    /**
    * Update the mode when language is auto
    */
    function update() {
        var mode = looksLike($editor.getValue());
        setMode(mode);
        setAutoOption("auto_" + mode,  "auto: " + findOption(mode).text());
    }

    /**
    * Set the auto option with the language
    * @param string value
    * @param string text
    */
    function setAutoOption(value, text){
        $optionSelected = $modeInput.find('option[value^="auto"]');
        $optionSelected.val(value);
        $optionSelected.text(text);
    }

    /**
     * @param  {string}
     * @return {jquery option selector}
     */
    function findOption(value){
        return $modeInput.find('option[value="' + value + '"]:first');
    }

    var $editor;
    var $modeInput;
    var $backInput;

    var autoDetection = 1;
    var language_editor_mode = {
        "c": "text/x-csrc",
        "c#": "text/x-csharp",
        "c++": "text/x-c++src",
        "clojure": "text/x-clojure",
        "coffeescript": "text/x-coffeescript",
        "css": "text/css",
        "d": "text/x-d",
        "diff": "text/x-diff",
        "erlang": "text/x-erlang",
        "go": "text/x-go",
        "groovy": "text/x-groovy",
        "haskell": "text/x-haskell",
        "html": "text/xml",
        "htmlmixed": "text/html",
        "http": "message/http",
        "java": "text/x-java",
        "javascript": "text/javascript",
        "json": "application/json",
        "less": "text/x-less",
        "lua": "text/x-lua",
        "markdown": "text/x-markdown",
        "nginx": "text/nginx",
        "perl": "text/x-perl",
        "php": "application/x-httpd-php",
        "plain text": "",
        "python": "text/x-python",
        "r": "text/x-rsrc",
        "ruby": "text/x-ruby",
        "scala": "text/x-scala",
        "shell": "text/x-sh",
        "smalltalk": "text/x-stsrc",
        "sql": "text/x-sql",
        "stex": "text/x-stex",
        "typescript": "application/typescript",
        "vbscript": "text/vbscript",
        "xml": "application/xml",
        "yaml": "text/x-yaml"
    };
    var auto_language = {
        "bash": "shell",
        "clojure": "clojure",
        "coffeescript": "coffeescript",
        "cpp": "c++",
        "cs": "c#",
        "css": "css",
        "d": "d",
        "diff": "diff",
        "erlang": "erlang",
        "go": "go",
        "groovy": "groovy",
        "haskell": "haskell",
        "http": "http",
        "java": "java",
        "javascript": "javascript",
        "json": "json",
        "less": "less",
        "lua": "lua",
        "markdown": "markdown",
        "nginx": "nginx",
        "perl": "perl",
        "php": "php",
        "python": "python",
        "r": "r",
        "ruby": "ruby",
        "scala": "scala",
        "shell": "shell",
        "smalltalk": "smalltalk",
        "sql": "sql",
        "tex": "stex",
        "typescript": "typescript",
        "vbscript": "vbscript",
        "xml": "xml",
        "yaml": "yaml",
    };

    var module = {
        init: init,
        selectMode: selectMode,
        val: val
    };

    return module;
}());
