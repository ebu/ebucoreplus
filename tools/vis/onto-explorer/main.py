
import os 
import streamlit as st
from rdflib import Graph, RDF, RDFS, OWL, URIRef, Literal
from ontology_helpers import *
from graph_helpers import build_graph_base
import tempfile
from config import grouped_main_classes, group_colors, get_class_color
from streamlit_searchbox import st_searchbox
from rapidfuzz import process

@st.cache_data
def load_ontology(uploaded_file):
    g = Graph()
    g.parse(uploaded_file, format="turtle")
    return g

def main():

    st.set_page_config(page_title="EBU Ontology Explorer", layout="wide", initial_sidebar_state="expanded")

    #st.title("EBU Ontology Explorer")
    logo_path = os.path.join(os.path.dirname(__file__), "static", "ebu_logo.svg")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=150)
    else:
        st.sidebar.markdown("### Ontology Explorer")


    st.sidebar.subheader("Step 1: Load Ontology")

    # Load pre-uploaded default file from example_data
    default_ontology_path = os.path.join(os.path.dirname(__file__), "example_data", "ebucoreplus-2-0.owl")
    uploaded_file = st.sidebar.file_uploader("Upload your Turtle (.ttl) or OWL file", type=["ttl", "owl"])

    if uploaded_file is None and os.path.exists(default_ontology_path):
        uploaded_file = default_ontology_path

    if uploaded_file is not None:
        try:
            g = load_ontology(uploaded_file)
            namespace_uri = "http://www.ebu.ch/metadata/ontologies/ebucoreplus#"
            main_classes_list = [label for group in grouped_main_classes.values() for label in group]

            # === Sidebar: Global class search ===
            st.sidebar.subheader("Global Class Search")

            all_class_uris = set(s for s in g.subjects(RDF.type, OWL.Class))
            dropdown = []
            for uri in all_class_uris:
                frag = pretty_print_uri(uri)
                lbls = list(g.objects(uri, RDFS.label))
                if re.match(r"^n[0-9a-f]{32}$", frag):
                    if lbls:
                        dropdown.append((get_class_display_label(g, uri), uri))
                else:
                    dropdown.append((get_class_display_label(g, uri), uri))

            dropdown = [(lbl, uri) for lbl, uri in dropdown if lbl and lbl.strip()]
            dropdown = sorted(dropdown, key=lambda x: x[0].lower())
            label_to_uri = {label: uri for label, uri in dropdown}

            def search_func(query):
                matches = process.extract(query, label_to_uri.keys(), limit=10)
                return [m[0] for m in matches if m[1] >= 50]

            fuzzy_label = st_searchbox(
                search_func,
                placeholder="Search class name...",
                label="Fuzzy Search",
                key="fuzzy_autocomplete"
            )

            dropdown_label = st.sidebar.selectbox("Or browse all classes", list(label_to_uri.keys()), key="global_fallback")

            # === Sidebar: Domain selection ===
            st.sidebar.markdown("---")
            st.sidebar.subheader("Main Class Browser")
            selected_group = st.sidebar.selectbox("Functional Domain", list(grouped_main_classes.keys()), key="domain_group")
            class_options = grouped_main_classes[selected_group]
            domain_label = st.sidebar.selectbox("Select class", class_options, key="domain_select")

            # === Class resolution priority based on user action ===
            if fuzzy_label:
                selected_class_label = fuzzy_label
                selected_class = label_to_uri[fuzzy_label]
                st.session_state["selection_source"] = "fuzzy"
            elif st.session_state.get("global_fallback") != st.session_state.get("last_global_fallback"):
                selected_class_label = dropdown_label
                selected_class = label_to_uri[dropdown_label]
                st.session_state["selection_source"] = "dropdown"
                st.session_state["last_global_fallback"] = dropdown_label
            elif st.session_state.get("domain_select") != st.session_state.get("last_domain_select"):
                selected_class_label = domain_label
                selected_class = URIRef(namespace_uri + domain_label)
                st.session_state["selection_source"] = "domain"
                st.session_state["last_domain_select"] = domain_label
            else:
                selected_class_label = domain_label
                selected_class = URIRef(namespace_uri + domain_label)

            if 'last_selected_class' not in st.session_state:
                st.session_state['last_selected_class'] = selected_class
            if selected_class != st.session_state['last_selected_class']:
                st.session_state['expand_level'] = 0
                st.session_state['last_selected_class'] = selected_class
            if 'expand_level' not in st.session_state:
                st.session_state['expand_level'] = 0

            if selected_class is None:
                st.info("Please select a class to display details.")
                st.stop()

            if not isinstance(selected_class, URIRef):
                st.error("Class selection failed: not a valid URI.")
                st.stop()

            st.info(f"Selected class: {selected_class_label}")

            subclasses = get_subclasses(g, selected_class)
            superclasses = get_superclasses(g, selected_class)
            restriction_props = get_restriction_properties(g, selected_class)
            reverse_links = get_reverse_restriction_properties(g, selected_class)
            labels, descriptions = get_skos_labels_and_descriptions(g, selected_class)
            broader, narrower = get_skos_broader_narrower(g, selected_class)

            tabs = st.tabs([
                "Graph View", "Overview", "Properties", "Reverse Properties",
                "Hierarchy View"
            ])


            with tabs[0]:

                st.subheader("Graph View")
                show_all_restrictions = st.checkbox("Show properties ", value=False)
                show_reverse_links = st.checkbox("Show incoming properties", value=False)

                cols = st.columns(2)
                if cols[0].button("Property View"):
                    st.session_state['expand_level'] = 0
                if cols[1].button("Class View"):
                    st.session_state['expand_level'] = -1

                expand_level = st.session_state.get('expand_level', 0)

                if expand_level == 0:

                    net = build_graph_base(
                        g, selected_class, subclasses, superclasses,
                        restriction_props, reverse_links, (broader, narrower),
                        main_classes_list,
                        expand_all=show_all_restrictions,
                        show_reverse_links=show_reverse_links
                        )

                     # Render graph

                    def patch_html_for_pinning(html_path):
                        with open(html_path, "r", encoding="utf-8") as f:
                            html = f.read()
                        pin_script = """
                        <script type="text/javascript">
                          network.on("dragEnd", function(params) {
                            if (params.nodes.length > 0) {
                              params.nodes.forEach(function(nodeId) {
                                network.body.data.nodes.update({id: nodeId, fixed: {x:true, y:true}});
                              });
                            }
                          });
                          network.on("doubleClick", function(params) {
                            if (params.nodes.length > 0) {
                              params.nodes.forEach(function(nodeId) {
                                network.body.data.nodes.update({id: nodeId, fixed: {x:false, y:false}});
                              });
                            }
                          });
                        </script>
                        """
                        html = html.replace("</body>", pin_script + "</body>")
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(html)

                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                   
                    net.save_graph(tmp_file.name)
                    patch_html_for_pinning(tmp_file.name)
                    st.components.v1.html(open(tmp_file.name, 'r', encoding='utf-8').read(), height=800, width=1600, scrolling=True)

                    # ---- Legend ----
                    st.markdown("### Main Classes Legend")
                    legend_html = ""
                    for group, color in group_colors.items():
                        legend_html += f'<span style="display:inline-block;width:20px;height:20px;background:{color};border-radius:5px;margin-right:8px;border:1px solid #333"></span> {group}<br>'
                    legend_html += '<span style="display:inline-block;width:20px;height:20px;background:red;border-radius:5px;margin-right:8px;border:1px solid #333"></span> Selected class<br>'
                    st.markdown(legend_html, unsafe_allow_html=True)


                elif expand_level == -1:

                    st.markdown("### Class Hierarchy Graph")
                    net = Network(height="700px", width="100%", notebook=False, directed=True)
                    net.set_options("""
                        {
                          "interaction": {"dragNodes": true, "dragView": true, "zoomView": true},
                          "physics": {"enabled": true, "barnesHut": {"springLength": 350}},
                          "nodes": {"font": {"size": 18}},
                          "edges": {"font": {"size": 16, "align": "top", "background": "white", "strokeWidth": 2}, "smooth": true}
                        }
                    """)

                    visited_up = set()
                    visited_down = set()

                    def add_superclasses(child):
                        if child in visited_up:
                            return
                        visited_up.add(child)
                        label = pretty_print_uri(child)
                        color = "red" if child == selected_class else get_class_color(label)
                        title = get_label_and_description(g, child)
                        net.add_node(str(child), label=label, title=title, color=color)
                        for parent in get_superclasses(g, child):
                            add_superclasses(parent)
                            net.add_edge(str(parent), str(child), label="Superclass", color="purple", arrows="to")

                    def add_subclasses(parent):
                        if parent in visited_down:
                            return
                        visited_down.add(parent)
                        label = pretty_print_uri(parent)
                        color = "red" if parent == selected_class else get_class_color(label)
                        title = get_label_and_description(g, parent)
                        net.add_node(str(parent), label=label, title=title, color=color)
                        for child in get_subclasses(g, parent):
                            add_subclasses(child)
                            net.add_edge(str(parent), str(child), label="Subclass", color="purple", arrows="to")

                    # Add the upward path (all ancestors)
                    add_superclasses(selected_class)
                    # Add the downward tree (all descendants)
                    add_subclasses(selected_class)

                    # Render graph
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                    net.save_graph(tmp_file.name)
                    st.components.v1.html(open(tmp_file.name, 'r', encoding='utf-8').read(), height=800, width=1600, scrolling=True)

                    # ---- Legend ----
                    st.markdown("### Main Classes Legend")
                    legend_html = ""
                    for group, color in group_colors.items():
                        legend_html += f'<span style="display:inline-block;width:20px;height:20px;background:{color};border-radius:5px;margin-right:8px;border:1px solid #333"></span> {group}<br>'
                    legend_html += '<span style="display:inline-block;width:20px;height:20px;background:red;border-radius:5px;margin-right:8px;border:1px solid #333"></span> Selected class<br>'
                    st.markdown(legend_html, unsafe_allow_html=True)


            with tabs[1]:  # Overview
                st.subheader("Class Overview")
                st.markdown(f"**Full URI:** `{selected_class}`")
                defined_by = list(g.objects(selected_class, RDFS.isDefinedBy))
                if defined_by:
                    st.markdown("**Reference/Defined by:**")
                    for ref in defined_by:
                        st.markdown(f"- [{ref}]({ref})")
                    st.info("This is a documentation/reference link, not inheritance.")

                # SKOS concept badge
                if is_skos_concept_class(g, selected_class):
                    st.success("This class is a SKOS Concept.")

                # SKOS & descriptive properties (only English)
                st.markdown("**Labels :**")
                english_labels = [l for l in g.objects(selected_class, RDFS.label) if getattr(l, 'language', None) == 'en']
                st.write([format_node(l) for l in english_labels] or "_None_")

                st.markdown("**Descriptions :**")
                english_descriptions = [d for d in g.objects(selected_class, URIRef("http://purl.org/dc/terms/description")) if getattr(d, 'language', None) == 'en']
                st.write([format_node(d) for d in english_descriptions] or "_None_")

                # Add SKOS-specific fields (optional: only English )
                skos_definitions = [str(d) for d in g.objects(selected_class, SKOS.definition) if getattr(d, 'language', None) == 'en']
                skos_examples = [str(e) for e in g.objects(selected_class, SKOS.example) if getattr(e, 'language', None) == 'en']
                if skos_definitions:
                    st.markdown("**SKOS Definitions:**")
                    st.write(skos_definitions)
                if skos_examples:
                    st.markdown("**SKOS Examples:**")
                    st.write(skos_examples)

                broader, narrower = get_skos_broader_narrower(g, selected_class)
                st.markdown("**Broader Concepts:**")
                st.write([format_node(b) for b in broader] or "_None_")
                st.markdown("**Narrower Concepts:**")
                st.write([format_node(n) for n in narrower] or "_None_")


            with tabs[2]:
                st.subheader("Properties")
                if restriction_props:
                    for prop, rtype, rvalue in restriction_props:
                        if rtype == "qualified_cardinality":
                            # Compose a readable and linked string
                            details = []
                            if rvalue["q_exact"]:
                                details.append(f"owl:qualifiedCardinality {rvalue['q_exact']}")
                            if rvalue["q_min"]:
                                details.append(f"owl:minQualifiedCardinality {rvalue['q_min']}")
                            if rvalue["q_max"]:
                                details.append(f"owl:maxQualifiedCardinality {rvalue['q_max']}")
                            if rvalue["on_class"]:
                                # Use your link-formatting function for on_class!
                                details.append(f"owl:onClass: {format_node(rvalue['on_class'])}")
                            detail_str = ", ".join(details)
                            st.markdown(f"- {format_node(prop)} ({detail_str})")
                        elif rtype and rvalue:
                            st.markdown(f"- {format_node(prop)} ({rtype}: {format_node(rvalue)})")
                        else:
                            st.markdown(f"- {format_node(prop)} (no range)")
                else:
                    st.write("_No restriction properties._")


            with tabs[3]:
                st.subheader("Reverse Properties")
                if reverse_links:
                    for src_cls, prop, rtype in reverse_links:
                        st.markdown(f"- {format_node(prop)} from {format_node(src_cls)} ({rtype})")
                else:
                    st.write("_No reverse restriction links._")

            # In your Hierarchy tab:
            with tabs[4]:
                st.subheader("Class Hierarchy")
                show_class_hierarchy_tree(g, selected_class)

              
        except Exception as e:
            st.error(f"⚠️ Error loading ontology: {e}")
    else:
        st.info("👈 Upload a Turtle file to begin.")

if __name__ == "__main__":
    main()
