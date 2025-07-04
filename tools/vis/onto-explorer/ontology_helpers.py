import re
import streamlit as st
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import SKOS
from pyvis.network import Network
import tempfile
import math
import pandas as pd
from rapidfuzz import process, fuzz
from config import grouped_main_classes, group_colors, get_class_color



def get_label_and_description(g, uri, max_length=200):
    labels = [str(lbl) for lbl in g.objects(uri, RDFS.label) if getattr(lbl, 'language', None) == 'en']
    descriptions = [str(desc) for desc in g.objects(uri, URIRef("http://purl.org/dc/terms/description")) if getattr(desc, 'language', None) == 'en']
    label_text = "; ".join(labels) if labels else "None"
    desc_text = "; ".join(descriptions) if descriptions else "None"
    if len(desc_text) > max_length:
        desc_text = desc_text[:max_length] + "..."
    return f"Label: {label_text}\nDescription: {desc_text}"

def get_transitive_superclasses(g, cls, visited=None):
    if visited is None:
        visited = set()
    supers = list(g.objects(cls, RDFS.subClassOf))
    all_supers = []
    for s in supers:
        if isinstance(s, URIRef) and s not in visited:
            visited.add(s)
            all_supers.append(s)
            all_supers.extend(get_transitive_superclasses(g, s, visited))
    return all_supers

def get_transitive_subclasses(g, cls, visited=None):
    if visited is None:
        visited = set()
    subs = list(g.subjects(RDFS.subClassOf, cls))
    all_subs = []
    for s in subs:
        if isinstance(s, URIRef) and s not in visited:
            visited.add(s)
            all_subs.append(s)
            all_subs.extend(get_transitive_subclasses(g, s, visited))
    return all_subs

def show_class_hierarchy(g, selected_class):
    st.markdown("### Superclasses")
    supers = get_transitive_superclasses(g, selected_class)
    if supers:
        for s in supers:
            st.markdown(f"- {format_node(s)}")
    else:
        st.write("_No superclasses found._")

    st.markdown("### Subclasses")
    subs = get_transitive_subclasses(g, selected_class)
    if subs:
        for s in subs:
            st.markdown(f"- {format_node(s)}")
    else:
        st.write("_No subclasses found._")

from collections import deque


def pretty_print_uri(uri):
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    elif "/" in uri_str:
        return uri_str.rstrip("/").split("/")[-1]
    return uri_str

def format_node(node):
    if isinstance(node, URIRef):
        return f"[{pretty_print_uri(node)}]({node})"
    elif isinstance(node, Literal):
        return f'"{node}"'
    else:
        return str(node)

def get_subclasses(g, cls):
    return sorted([s for s in g.subjects(RDFS.subClassOf, cls) if isinstance(s, URIRef)])

def get_superclasses(g, cls):
    return sorted([s for s in g.objects(cls, RDFS.subClassOf) if isinstance(s, URIRef)])

def get_reverse_restriction_properties(g, target_class):
    links = []
    for cls in g.subjects(RDF.type, OWL.Class):
        for restriction in g.objects(cls, RDFS.subClassOf):
            if (restriction, RDF.type, OWL.Restriction) in g:
                prop = next(g.objects(restriction, OWL.onProperty), None)
                if (restriction, OWL.allValuesFrom, target_class) in g:
                    links.append((cls, prop, "owl:allValuesFrom"))
                elif (restriction, OWL.someValuesFrom, target_class) in g:
                    links.append((cls, prop, "owl:someValuesFrom"))
                elif (restriction, OWL.hasValue, target_class) in g:
                    links.append((cls, prop, "owl:hasValue"))
                # catch owl:onClass!
                elif (restriction, OWL.onClass, target_class) in g:
                    links.append((cls, prop, "owl:onClass"))
    return links


def is_skos_concept_class(g, cls):
    return (cls, RDFS.subClassOf, SKOS.Concept) in g

def get_skos_labels_and_descriptions(g, cls):
    labels = [l for l in g.objects(cls, RDFS.label) if getattr(l, 'language', None) == 'en']
    descriptions = [d for d in g.objects(cls, URIRef("http://purl.org/dc/terms/description")) if getattr(d, 'language', None) == 'en']
    return labels, descriptions

def get_skos_broader_narrower(g, cls):
    broader = list(g.objects(cls, SKOS.broader))
    narrower = list(g.objects(cls, SKOS.narrower))
    return broader, narrower

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

def has_human_label(g, uri):
    return any(g.objects(uri, RDFS.label))

def get_class_display_label(g, uri):

    # Namespace to prefix mapping
    nsmap = {
    "http://www.ebu.ch/metadata/ontologies/ebucoreplus#": "ec",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://purl.org/dc/terms/": "dcterms",
    "http://www.w3.org/2004/02/skos/core#": "skos",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    }

    uri_str = str(uri)
    prefix = None
    frag = pretty_print_uri(uri)
    for ns, pre in nsmap.items():
        if uri_str.startswith(ns):
            prefix = pre
            local = uri_str[len(ns):]
            break
    if not prefix:
        # Fallback to just fragment if unknown namespace
        prefix = ""
        local = frag
    label = None
    lbls = list(g.objects(uri, RDFS.label))
    for l in lbls:
        if getattr(l, 'language', None) == 'en':
            label = str(l)
            break
    if not label and lbls:
        label = str(lbls[0])
    if label:
        return f"{label} ({prefix}:{local})" if prefix else f"{label} ({local})"
    else:
        return f"{prefix}:{local}" if prefix else local

def get_all_connected_classes(g, selected_class):
    connected = set()
    # Outgoing links
    for p, o in g.predicate_objects(selected_class):
        if isinstance(o, URIRef):
            connected.add(o)
    # Incoming links
    for s, p in g.subject_predicates(selected_class):
        if isinstance(s, URIRef):
            connected.add(s)
    return connected

def get_nodes_and_all_edges_within_n_hops(g, start_class, hops=1):
    from collections import deque

    nodes = set([start_class])
    queue = deque([(start_class, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth >= hops:
            continue
        # Outgoing
        for p, o in g.predicate_objects(current):
            if isinstance(o, URIRef) and o not in nodes:
                nodes.add(o)
                queue.append((o, depth+1))
        # Incoming
        for s, p in g.subject_predicates(current):
            if isinstance(s, URIRef) and s not in nodes:
                nodes.add(s)
                queue.append((s, depth+1))
    edges = []
    for src in nodes:
        for p, tgt in g.predicate_objects(src):
            if isinstance(tgt, URIRef) and tgt in nodes and str(p) != str(RDF.type):
                edges.append((src, p, tgt))
    return nodes, edges

def get_connected_subgraph_bfs(g, start_class, hops=2):
    """
    Return the set of nodes and edges reachable from start_class within 'hops' steps (BFS).
    Only nodes actually connected by at least one edge will appear.
    """
    from collections import deque

    visited_nodes = set([start_class])
    edges = []
    queue = deque([(start_class, 0)])

    while queue:
        current, depth = queue.popleft()
        if depth >= hops:
            continue
        # Outgoing edges
        for p, o in g.predicate_objects(current):
            if isinstance(o, URIRef):
                edges.append((current, p, o))
                if o not in visited_nodes:
                    visited_nodes.add(o)
                    queue.append((o, depth + 1))
        # Incoming edges
        for s, p in g.subject_predicates(current):
            if isinstance(s, URIRef):
                edges.append((s, p, current))
                if s not in visited_nodes:
                    visited_nodes.add(s)
                    queue.append((s, depth + 1))
    return visited_nodes, edges

def get_restriction_properties(g, cls):
    props = []
    for restriction in g.objects(cls, RDFS.subClassOf):
        if (restriction, RDF.type, OWL.Restriction) in g:
            prop = next(g.objects(restriction, OWL.onProperty), None)
            range_all = next(g.objects(restriction, OWL.allValuesFrom), None)
            range_some = next(g.objects(restriction, OWL.someValuesFrom), None)
            range_has = next(g.objects(restriction, OWL.hasValue), None)
            # Qualified cardinality patterns
            q_min = next(g.objects(restriction, OWL.minQualifiedCardinality), None)
            q_max = next(g.objects(restriction, OWL.maxQualifiedCardinality), None)
            q_exact = next(g.objects(restriction, OWL.qualifiedCardinality), None)
            on_class = next(g.objects(restriction, OWL.onClass), None)

            if prop:
                if range_all:
                    props.append((prop, "owl:allValuesFrom", range_all))
                elif range_some:
                    props.append((prop, "owl:someValuesFrom", range_some))
                elif range_has:
                    props.append((prop, "owl:hasValue", range_has))
                elif q_exact or q_min or q_max:
                    props.append((
                        prop,
                        "qualified_cardinality",
                        {
                            "q_exact": q_exact,
                            "q_min": q_min,
                            "q_max": q_max,
                            "on_class": on_class
                        }
                    ))
                else:
                    props.append((prop, None, None))
    return props

def get_ancestor_path(g, node):
    path = []
    current = node
    visited = set()
    while True:
        supers = get_superclasses(g, current)
        if supers and supers[0] not in visited:
            current = supers[0]
            path.insert(0, current)
            visited.add(current)
        else:
            break
    path.append(node)
    return path


def get_ancestors_path(g, node):
    """Return the list of ancestor nodes from the topmost superclass to the node itself."""
    path = []
    current = node
    visited = set()
    while True:
        supers = get_superclasses(g, current)
        if supers and supers[0] not in visited:
            current = supers[0]
            path.insert(0, current)
            visited.add(current)
        else:
            break
    path.append(node)
    return path

def print_subtree_with_uris(g, node, prefix="", selected_class=None):
    # Subclasses, direct only
    subclasses = get_subclasses(g, node)
    for i, sub in enumerate(subclasses):
        is_selected = (sub == selected_class)
        color_style = "color:red; font-weight:bold;" if is_selected else ""
        label = pretty_print_uri(sub)
        uri = str(sub)
        st.markdown(
            f"{prefix} &nbsp;&nbsp;&nbsp; <span style='{color_style}'>{label}</span> &nbsp; <span style='font-size:12px; color:grey'>{uri}</span>",
            unsafe_allow_html=True
        )
        print_subtree_with_uris(g, sub, prefix + "&nbsp;&nbsp;&nbsp;&nbsp;", selected_class)

def show_ancestor_path(g, node, selected_class):
    path = []
    current = node
    visited = set()
    while True:
        supers = get_superclasses(g, current)
        if supers and supers[0] not in visited:
            current = supers[0]
            path.insert(0, current)
            visited.add(current)
        else:
            break
    path.append(node)
    for i, ancestor in enumerate(path):
        indent = '-' * i  # 0, 1, 2, ...
        is_selected = (ancestor == selected_class)
        color = "red" if is_selected else "#222"
        weight = "bold" if is_selected else "normal"
        label = pretty_print_uri(ancestor)
        uri = str(ancestor)
        st.markdown(
            f"{indent} <a href='{uri}' style='color:{color};font-weight:{weight};text-decoration:underline'>{label}</a>",
            unsafe_allow_html=True
        )
    return len(path)  # so we know how deep the indent is

def print_subtree_links(g, node, level=0, selected_class=None):
    subclasses = get_subclasses(g, node)
    for sub in subclasses:
        is_selected = (sub == selected_class)
        color = "red" if is_selected else "#222"
        weight = "bold" if is_selected else "normal"
        label = pretty_print_uri(sub)
        uri = str(sub)
        indent = '-' * (level+1)  # child of current
        st.markdown(
            f"{indent} <a href='{uri}' style='color:{color};font-weight:{weight};text-decoration:underline'>{label}</a>",
            unsafe_allow_html=True
        )
        print_subtree_links(g, sub, level=level+1, selected_class=selected_class)


def print_ascii_tree(g, node, selected_class, prefix="", is_last=True):
    # Prefix: "" for root, "   " for next, etc.
    label = pretty_print_uri(node)
    uri = str(node)
    if node == selected_class:
        # Red + bold for selected class
        rendered = f"<span style='color:red;font-weight:bold'><a href='{uri}' style='color:red;text-decoration:underline'>{label}</a></span>"
    else:
        rendered = f"<a href='{uri}' style='color:#222;text-decoration:underline'>{label}</a>"

    branch = "└─" if is_last else "├─"
    st.markdown(f"{prefix}{branch} {rendered}", unsafe_allow_html=True)

    children = get_subclasses(g, node)
    for i, child in enumerate(children):
        next_prefix = prefix + ("   " if is_last else "│  ")
        print_ascii_tree(g, child, selected_class, next_prefix, i == len(children)-1)

def is_descendant(g, node, target):
    if node == target:
        return True
    for child in get_subclasses(g, node):
        if is_descendant(g, child, target):
            return True
    return False

def get_top_ancestor(g, node):
    supers = get_superclasses(g, node)
    if supers:
        return get_top_ancestor(g, supers[0])
    return node

def show_class_hierarchy_tree(g, selected_class):
    def get_label_or_local(uri):
        for l in g.objects(uri, RDFS.label):
            if getattr(l, 'language', None) == 'en':
                return str(l)
        return pretty_print_uri(uri)

    def get_ancestry_list(g, cls):
        # Return [root, ..., selected_class]
        path = []
        while True:
            parents = [p for p in g.objects(cls, RDFS.subClassOf) if isinstance(p, URIRef)]
            if not parents:
                break
            parent = parents[0]  # Just pick one (if multiple, could be improved)
            path.append(parent)
            cls = parent
        return path[::-1] + [selected_class]

    def print_tree_with_ancestry(g, ancestry, idx=0, prefix=""):
        node = ancestry[idx]
        label = get_label_or_local(node)
        url = str(node)
        is_last = (idx == len(ancestry) - 1)
        branch = "└─ " if is_last else "├─ "
        html_label = f'<a href="{url}">{label}</a>'
        if is_last:  # Target class in red
            html_label = f'<span style="color:red">{html_label}</span>'
        st.markdown(f"{prefix}{branch}{html_label}", unsafe_allow_html=True)
        # If not at end of ancestry, go down ancestry
        if not is_last:
            next_prefix = prefix + ("   " if not is_last else "   ")
            print_tree_with_ancestry(g, ancestry, idx+1, next_prefix)
        else:
            # Print all subclasses of selected_class as tree
            print_subtree(g, node, prefix + "   ")

    def print_subtree(g, node, prefix=""):
        subclasses = [s for s in g.subjects(RDFS.subClassOf, node) if isinstance(s, URIRef)]
        subclasses = sorted(subclasses, key=lambda u: get_label_or_local(u).lower())
        for i, sub in enumerate(subclasses):
            last = (i == len(subclasses) - 1)
            branch = "└─ " if last else "├─ "
            next_prefix = prefix + ("   " if last else "│  ")
            label = get_label_or_local(sub)
            url = str(sub)
            html_label = f'<a href="{url}">{label}</a>'
            st.markdown(f"{prefix}{branch}{html_label}", unsafe_allow_html=True)
            print_subtree(g, sub, next_prefix)

    # 1. Build ancestry path from root to selected_class
    ancestry = get_ancestry_list(g, selected_class)
    print_tree_with_ancestry(g, ancestry)

def show_class_hierarchy_tree(g, selected_class):
    def get_label_or_local(uri):
        for l in g.objects(uri, RDFS.label):
            if getattr(l, 'language', None) == 'en':
                return str(l)
        return pretty_print_uri(uri)

    def get_superclass(g, node):
        supers = [p for p in g.objects(node, RDFS.subClassOf) if isinstance(p, URIRef)]
        return supers[0] if supers else None

    def build_ancestor_path(g, node):
        # Returns [root, ..., selected_class]
        path = []
        while True:
            parent = get_superclass(g, node)
            if parent is None:
                break
            path.append(parent)
            node = parent
        return path[::-1]  # root-first

    def print_ancestor_chain_with_tree(g, path, target, prefix="", visited=None):
        # Print each ancestor in path as one chain; then expand the selected node as a tree
        if visited is None:
            visited = set()
        if not path:
            # Reached selected_class
            print_hierarchy_subtree(g, target, prefix=prefix, selected_class=target, visited=visited)
            return
        node = path[0]
        label = get_label_or_local(node)
        url = str(node)
        st.markdown(f"{prefix}└─ <a href='{url}'>{label}</a>", unsafe_allow_html=True)
        print_ancestor_chain_with_tree(g, path[1:], target, prefix + "   ", visited=visited)

    def print_hierarchy_subtree(g, node, prefix="", selected_class=None, visited=None):
        if visited is None:
            visited = set()
        label = get_label_or_local(node)
        url = str(node)
        # Print the selected class in red, others normally
        if node == selected_class:
            st.markdown(f"{prefix}└─ <span style='color:red'><a href='{url}'>{label}</a></span>", unsafe_allow_html=True)
        else:
            st.markdown(f"{prefix}└─ <a href='{url}'>{label}</a>", unsafe_allow_html=True)
        # Print subclasses
        subclasses = [s for s in g.subjects(RDFS.subClassOf, node) if isinstance(s, URIRef)]
        subclasses = sorted(subclasses, key=lambda u: get_label_or_local(u).lower())
        for idx, sub in enumerate(subclasses):
            if sub in visited:
                continue
            visited.add(sub)
            last = idx == len(subclasses) - 1
            branch = "└─ " if last else "├─ "
            print_hierarchy_subtree(g, sub, prefix + ("   " if last else "│  "), selected_class=None, visited=visited)

    # Build the ancestor chain up to the selected class
    ancestor_path = build_ancestor_path(g, selected_class)
    # Print the chain, then expand the tree below
    print_ancestor_chain_with_tree(g, ancestor_path, selected_class)


