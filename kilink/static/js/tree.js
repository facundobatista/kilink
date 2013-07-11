var myTree = null;

function CreateTree() {
    myTree = new ECOTree('myTree','myTreeContainer');
    myTree.config.selectMode = ECOTree.SL_SINGLE;
    myTree.config.nodeFill = ECOTree.NF_FLAT;
    myTree.config.defaultNodeWidth = 25;
    myTree.config.defaultNodeHeight = 25;

    myTree.config.linkColor = '#556B00';


    for(var node in node_list) {
        //[order, parent, revno, url, tstamp] = node_list[node];
        no = node_list[node];
        order = no[0];
        parent = no[1];
        revno = no[2];
        url = no[3];
        tstamp = no[4];
        if (current_revno == revno){
            myTree.add(revno, parent, order, 0, 0, '#FBD400', 'black', url);
        } else {
            myTree.add(revno, parent, order, 0, 0, '#A38B00', 'blue', url);
        }
    }
    myTree.UpdateTree();
}
