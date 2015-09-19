var source = new EventSource('/api/1/linkodes/stream');
$(document).ready(function(){
    get_node_list()
    source.onmessage = function (event) {
         console.log(event.data);
    };
})


function get_node_list(){
    if(kid_info != ""){
        $.get("/api/1/linkodes/nodes/" + kid_info, function(data) {
            if (data !== false) {
                node_list = data.tree
                create_tree();
            }
        });
    }


}

function create_tree(){
        var tree_size = {};
        var layout_size = {};
        tree_size.width = 200;
        tree_size.height = 200;
        layout_size.width = 200;
        layout_size.height = 400;
        $(".klk-tree").empty();
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
                    window.location = node.url;
                };
        });
    }