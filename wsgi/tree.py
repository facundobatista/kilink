#!/usr/bin/env python
import matplotlib.pyplot as plt
import networkx as nx
import random
import backend

G=nx.DiGraph()

for a in backend.get_kilink('sdkjj'):
    G.add_node(a.id)
    if a.parent_revno > 0 :
        G.add_edge(a.id,a.parent_revno)

pos=nx.graphviz_layout(G,prog="dot")
nx.draw(G,pos)
plt.savefig("tree.png")
#plt.show()
#nx.draw_graphviz(G)
#nx.write_dot(G,'tree.dot')
