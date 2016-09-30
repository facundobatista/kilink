var linkode = (function (){

    /**
    * Init the module
    * @param {Dict} opts
    */
    function init(opts){
        $code_area = $("#" + opts.code_area);
        $form = $("#" + opts.form);
        $time_stamp = $("#" + opts.time_stamp);
        time_stamp_text = opts.time_stamp_text;
        node_list = opts.node_list;

        if (node_list !== false) {
            create_tree();
            $.each($(".node"), function() {
                $(this).tooltipster({
                    trigger: 'hover',
                    content: "See node's version " + $(this).text(),
                });
            });
        }

        $code_area.bind('keydown', 'ctrl+return', function(e) {
            $form.submit();
        });

        $time_stamp.text(time_stamp_text);
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
            .children(function(d)
            {
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
            .projection(function(d)
            {
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
            .attr("transform", function(d)
            {
                var dy = d.y + 40;
                return "translate(" + d.x + "," + dy + ")";
            });

        nodeGroup.append("svg:circle")
            .attr("class", "node-dot")
            .attr("r", 15)
            .style("fill", function(d)
            {
                if (d.selected) {
                   return "#222222";
                } else {
                   return "#AAAAAA";
                }

            });

        nodeGroup.append("svg:text")
            .attr("text-anchor", "middle")
            .attr("class", "node-text")
            .attr("dy", 5)
            .text(function(d)
            {
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
    */
    function select_node(node){
        window.location = node.url;
    }

    // selectors
    var $code_area;
    var $form;
    var $time_stamp;

    // values
    var time_stamp_text;
    var node_list;


    var module = {
        init: init,
    }

    return module;

}())
