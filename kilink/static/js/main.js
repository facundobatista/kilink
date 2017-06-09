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
        text_post_error_noty = opts.text_post_error_noty;
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

        $("#toggle-container").on("click", toggleTree);
        $("#btn-submit").on("click", api_post);
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
     */
    function api_post(event, current_retry){
        var api_post_url = API_URL;
        text_type = $("#selectlang").val().replace("auto_", "");
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
                if (current_retry < RETRY_TIMES){
                    retry_delay = RETRY_DELAYS[current_retry];
                    current_retry++;
                    show_retry_noty(retry_delay);
                    setTimeout(function(){
                        api_post(event, current_retry);
                    }, retry_delay);
                }
                else{
                    show_error_noty(text_post_error_noty, api_post, [event, ]);
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
                    if(first_load){
                        first_load_success = false;
                        show_error_noty(text_get_error_noty, api_get,
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
                            show_error_noty(text_get_error_noty, 
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
        $("#selectlang option[value^='auto']").text("auto")
        $("#selectlang option[value^='auto']").val("auto")
        $("#selectlang").val(text_type);
        editor.selectMode();
        set_timestamp(timestamp);
        editor.val(content);
    }

    /**
     * Toggle the tree panel
     */
    function toggleTree(force_open){
        var cp = $(".code-panel");
        var tp =$(".tree-panel");

        if (force_open){
            cp.removeClass("col-md-12").addClass("col-md-10");
            tp.show();
            $("#toogle-image").attr("src", close_tree_img);
            $("#toogle-image").tooltipster("content", closed_tree_tooltip);
            return;
        }

        if(cp.hasClass("col-md-12")){
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
     * @param  {nodeGroup}
     */
    function select_node(node){
        if (!node.selected){
            api_get(node.linkode_id, false, false, 0);
        }
    }

    /**
     * Unselect all kilinks
     * @param  {nodeGroup}
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
     * @param  {string} error Error message
     */
    function show_error_noty(error, retry_func, retry_params){
        var n = new Noty({
                type: 'error',
                text: error,
                killer: true,
                buttons:[
                    Noty.button(text_retry_button, 'btn btn-error', function(){
                        n.close();
                        //retry_func(...retry_params); // Spread Operator only ES6
                        retry_func.apply(null,retry_params); // ES5 Spread Operator solution
                    })
                ],
            }).show();
    }

    /**
     * Set the default values for noty
     */
    function noty_default(){
        Noty.overrideDefaults({
            theme: 'bootstrap-v3',
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
     * @return {[type]} [description]
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
    var text_post_error_noty;
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
        if (cmode == "auto" || cmode.startsWith("auto_")){
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
        var clang = langLike(info.language);
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
        var modeval = langMode == 'clike' ? 'c++' : langMode;
        $modeInput.find("option:selected").val("auto_"+modeval);
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
    var $modeInput;
    var $backInput;

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
        val: val
    };

    return module;
}());
