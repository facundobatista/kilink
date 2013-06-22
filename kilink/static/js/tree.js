var myTree = null;

function CreateTree() {
    myTree = new ECOTree('myTree','myTreeContainer');
    myTree.config.selectMode = ECOTree.SL_SINGLE;
    myTree.config.nodeFill = ECOTree.NF_FLAT;
    myTree.config.defaultNodeWidth = 25;
    myTree.config.defaultNodeHeight = 25;

    myTree.config.linkColor = '#556B00';


    for(var node in node_list) {
        //[parent, revno, url, tstamp] = node_list[node];
        no = node_list[node];
        parent = no[0];
        revno = no[1];
        url = no[2];
        tstamp = no[3];
        if (current_revno == revno){
            myTree.add(parseInt(revno), parent, revno, 0, 0, '#FBD400', 'black', url);
        } else {
            myTree.add(parseInt(revno), parent, revno, 0, 0, '#A38B00', 'blue', url);
        }
    }
    myTree.UpdateTree();
}
