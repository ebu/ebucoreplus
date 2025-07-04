# graph_helpers.py

from pyvis.network import Network
from ontology_helpers import pretty_print_uri, get_label_and_description
from config import grouped_main_classes, group_colors, get_class_color


def build_graph_base(
    g,
    class_uri,
    subclasses,
    superclasses,
    restriction_props,
    reverse_links,
    skos_info,
    main_classes_list=None,
    expand_all=False,              
    show_reverse_links=False       
):
    net = Network(height="700px", width="100%", notebook=False, directed=True)
    net.set_options("""
        {
          "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -6000,
              "centralGravity": 0.001,
              "springLength": 350,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 1
            },
            "minVelocity": 0.75,
            "stabilization": {
              "enabled": true,
              "iterations": 250
            }
          },
          "nodes": {
            "font": {
              "size": 18
            }
          },
          "edges": {
            "font": {
              "size": 16,
              "align": "top",
              "background": "white",
              "strokeWidth": 2
            },
            "smooth": true
          }
        }
    """)

    def add_node_with_metadata(uri, color=None):
        label = pretty_print_uri(uri)
        node_color = color or get_class_color(label)
        title = get_label_and_description(g, uri)
        net.add_node(str(uri), label=label, title=title, color=node_color)

    add_node_with_metadata(class_uri, color="red")

    # Subclasses and superclasses (always shown)
    for sub in subclasses:
        add_node_with_metadata(sub)
        net.add_edge(str(class_uri), str(sub), title="Subclass", label="Subclass", color="purple", arrows="to", smooth=True)
    for sup in superclasses:
        add_node_with_metadata(sup)
        net.add_edge(str(sup), str(class_uri), title="Superclass", label="Superclass", color="purple", arrows="to", smooth=True)

    # Add restriction-based edges (only if expand_all)
    if expand_all:
        for prop, rtype, rvalue in restriction_props:
            if rtype == "qualified_cardinality" and isinstance(rvalue, dict):
                if rvalue["on_class"]:
                    add_node_with_metadata(rvalue["on_class"])
                    prop_label = pretty_print_uri(prop)
                    net.add_edge(
                        str(class_uri), str(rvalue["on_class"]),
                        title=prop_label, label=prop_label, color="blue", arrows="to", smooth=True,
                        font={"size": 16, "align": "top", "background": "white", "strokeWidth": 2}
                    )
            elif rvalue:
                add_node_with_metadata(rvalue)
                prop_label = pretty_print_uri(prop)
                net.add_edge(
                    str(class_uri), str(rvalue),
                    title=prop_label, label=prop_label, color="blue", arrows="to", smooth=True,
                    font={"size": 16, "align": "top", "background": "white", "strokeWidth": 2}
                )

    if show_reverse_links:
        for src_cls, prop, _ in reverse_links:
            add_node_with_metadata(src_cls)
            prop_label = pretty_print_uri(prop)
            net.add_edge(
                str(src_cls), str(class_uri),
                title=prop_label, label=prop_label, color="blue", arrows="to", smooth=True,
                font={"size": 16, "align": "top", "background": "white", "strokeWidth": 2}
            )

    # SKOS broader/narrower
    broader, narrower = skos_info
    for b in broader:
        add_node_with_metadata(b, color="green")
        net.add_edge(str(b), str(class_uri), title="broader", label="broader", smooth=True, font={"size": 16, "align": "top", "background": "white", "strokeWidth": 2})
    for n in narrower:
        add_node_with_metadata(n, color="green")
        net.add_edge(str(class_uri), str(n), title="narrower", label="narrower", smooth=True, font={"size": 16, "align": "top", "background": "white", "strokeWidth": 2})

    return net
