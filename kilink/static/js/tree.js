var myTree = null;

function CreateTree() {
    myTree = new ECOTree('myTree','myTreeContainer');
    myTree.config.selectMode = ECOTree.SL_SINGLE;
    myTree.config.nodeFill = ECOTree.NF_FLAT;
    myTree.config.defaultNodeWidth = 25;
    myTree.config.defaultNodeHeight = 25;

    myTree.config.linkColor = '#556B00';

    for(nodo in nodo_list) {
        [parent, revno, url, tstamp] = nodo;

        if (current_revno == revno){
            myTree.add(revno, parent, revno.toString(), 0, 0, '#FBD400', 'black');
        } else {
            myTree.add(revno, parent, revno.toString(), 0, 0, '#A38B00', 'blue', url);
        }
    }
    myTree.UpdateTree();
}
