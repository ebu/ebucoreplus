import os
import streamlit as st
from rdflib import Graph, RDF, RDFS, OWL, URIRef
from collections import defaultdict
import pandas as pd
import math
from helpers import pretty, build_class_stats, extract_edges, class_nice_view, compare_object_properties
from PIL import Image


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(CURRENT_DIR, "static", "ebu_logo.svg")

logo_width_px = 120

col1, col2 = st.columns([0.25, 0.75])

with col1:
    try:
        st.image(logo_path, width=logo_width_px)
    except Exception:
        st.write("EBU Logo")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  
    st.title("Ontology Diff Analyzer")


# ---------- Streamlit UI ---------------------------------------------


default_old = "example_data/ebucoreplus-1-07.ttl"
default_new = "example_data/ebucoreplus-2-0.ttl"

# Try to open default files as fallback
def get_default_file_bytes(filepath):
    with open(filepath, "rb") as f:
        return f.read()

# Sidebar
st.sidebar.markdown("### Upload ontology versions (optional)")
file_old = st.sidebar.file_uploader("Old version ", type=["ttl"])
file_new = st.sidebar.file_uploader("New version ", type=["ttl"])

if not file_old:
    if os.path.exists(default_old):
        file_old = get_default_file_bytes(default_old)
        #st.sidebar.info(f"Loaded default: {default_old}")
if not file_new:
    if os.path.exists(default_new):
        file_new = get_default_file_bytes(default_new)
        #st.sidebar.info(f"Loaded default: {default_new}")



g_old = Graph()
g_old.parse(data=file_old, format="turtle")
g_new = Graph()
g_new.parse(data=file_new, format="turtle")

st.sidebar.write("### Loaded files:")
st.sidebar.write(f"Old: {getattr(file_old, 'name', default_old)}")
st.sidebar.write(f"New: {getattr(file_new, 'name', default_new)}")


df_old = build_class_stats(g_old)
df_new = build_class_stats(g_new)

# --- diff of classes --------------------------------------------------
df_old["key"] = df_old["URI"]
df_new["key"] = df_new["URI"]

cmp = df_new.merge(df_old, on="key", how="outer", suffixes=("_new", "_old"))

def status(row):
    if pd.isna(row["Label_old"]):
        return "New"
    if pd.isna(row["Label_new"]):
        return "Removed"
    if row["Subclasses_new"] != row["Subclasses_old"] or row["TotalRelations_new"] != row["TotalRelations_old"]:
        return "Modified"
    return "Unchanged"

cmp["Status"] = cmp.apply(status, axis=1)

valid_uris = set(df_new["URI"])
new_nodes = {
    uri for uri in cmp.loc[cmp["Status"] == "New", "URI_new"]
    if uri in valid_uris
}
removed_nodes = set(cmp.loc[cmp["Status"] == "Removed", "URI_old"])

# edges
classes_new = {URIRef(u) for u in df_new["URI"]}
classes_old = {URIRef(u) for u in df_old["URI"]}

edges_new = extract_edges(g_new, classes_new)
edges_old = extract_edges(g_old, classes_old)

added_edges = len(edges_new - edges_old)
removed_edges = len(edges_old - edges_new)

# --- Delta dashboard metrics for classes and relations ---
st.subheader("Delta dashboard")
c1, c2, c3 = st.columns(3)
c1.metric("➕ Classes", len(new_nodes))
c2.metric("➖ Classes", len(removed_nodes))
c3.metric("⚙️  Modified", (cmp["Status"] == "Modified").sum())

d1, d2 = st.columns(2)
d1.metric("➕ Relations", added_edges)
d2.metric("➖ Relations", removed_edges)

# ----------- Grouped domains and domain mapping -----------
grouped_main_classes = {
    "Content & Editorial Structure": [
        "Asset", "EditorialObject", "EditorialSegment", "Picture", "Essence", "TimelineTrack"
    ],
    "Audience & Analytics": [
        "Audience", "Consumer", "ConsumptionEvent", "ConsumptionCount",
        "ConsumptionDevice", "ConsumptionDeviceProfile", "ResonanceEvent", "ResonanceCount"
    ],
    "Production & Workflow": [
        "ProductionJob", "ProductionDevice", "ProductionOrder", "AudioProgramme"
    ],
    "Rights & Legal": [
        "Contract", "Licence", "Rights"
    ],
    "Publication & Distribution": [
        "PublicationPlan", "PublicationChannel", "PublicationPlatform",
        "PublicationEvent", "PublicationService"
    ],
    "Marketing & Engagement": [
        "Campaign"
    ],
    "Actors & Agents": [
        "Account", "Agent"
    ],
    "Concepts & Semantics": [
        "Concept", "Resource"
    ]
}
label2dom = {}
ns = "http://www.ebu.ch/metadata/ontologies/ebucoreplus#"
for dom, labels in grouped_main_classes.items():
    for lbl in labels:
        label2dom[f"{ns}{lbl}"] = dom
df_old["Domain"] = df_old["URI"].map(label2dom).fillna("Other")
df_new["Domain"] = df_new["URI"].map(label2dom).fillna("Other")

# -------------- Tabs UI --------------
tab_labels = [
    "Classes - modified",
    "Classes - new",
    "Classes - removed",
    "Relations",
    "Overview of New Classes",
    "Overview of New Relations"
]
tabs = st.tabs(tab_labels)

# -------- Per-class differences: MODIFIED -----------
with tabs[0]:
    st.subheader("Classes - modified")
    mod_df = cmp.loc[cmp["Status"] == "Modified"]
    if mod_df.empty:
        st.info("No modified classes.")
    else:
        for _, row in mod_df.iterrows():
            lbl = row["Label_new"]
            with st.expander(lbl):
                st.write("URI (v2):", row.get("URI_new", "—"))
                st.write("URI (v1):", row.get("URI_old", "—"))
                st.markdown(
                    f"- Subclasses **{row['Subclasses_old']} → {row['Subclasses_new']}**  \n"
                    f"- ObjectProperties **{row['ObjectProperties_old']} → {row['ObjectProperties_new']}**  \n"
                    f"- TotalRelations **{row['TotalRelations_old']} → {row['TotalRelations_new']}**"
                )
                uri = row.get("URI_new", None)
                if uri:
                    added, removed = compare_object_properties(g_new, g_old, uri)
                    if added:
                        st.write("**New object properties in v2:**")
                        for p in added:
                            st.write(f"- {pretty(p)}")
                    if removed:
                        st.write("**Object properties removed since v1:**")
                        for p in removed:
                            st.write(f"- {pretty(p)}")


# -------- Per-class differences: NEW -----------

with tabs[1]:
    st.subheader("Classes - new")
    new_df = cmp.loc[cmp["Status"] == "New"]
    if new_df.empty:
        st.info("No new classes.")
    else:
        for _, row in new_df.iterrows():
            lbl = row["Label_new"]
            with st.expander(lbl):
                uri = row.get("URI_new", None)
                if uri:
                    st.markdown(class_nice_view(g_new, uri))

# -------- Per-class differences: REMOVED -----------
with tabs[2]:
    st.subheader("Classes - removed")
    rem_df = cmp.loc[cmp["Status"] == "Removed"]
    if rem_df.empty:
        st.info("No removed classes.")
    else:
        for _, row in rem_df.iterrows():
            lbl = row["Label_old"]
            with st.expander(lbl):
                uri = row.get("URI_old", None)
                if uri:
                    st.markdown(class_nice_view(g_old, uri))


# -------- Per-relation differences by class (object properties only) -----------
with tabs[3]:
    st.subheader("Relations")
    SUBCLASS_PRED = URIRef("subClassOf")
    def filter_non_subclassof(edges):
        return [e for e in edges if e[1] != SUBCLASS_PRED]
    changed_classes = set()
    for subj, pred, obj in filter_non_subclassof(edges_new - edges_old):
        changed_classes.add(subj)
        changed_classes.add(obj)
    for subj, pred, obj in filter_non_subclassof(edges_old - edges_new):
        changed_classes.add(subj)
        changed_classes.add(obj)
    class_label_map = {URIRef(row['URI_new']): row['Label_new'] for _, row in cmp.iterrows() if pd.notna(row['URI_new'])}
    class_label_map.update({URIRef(row['URI_old']): row['Label_old'] for _, row in cmp.iterrows() if pd.notna(row['URI_old'])})
    def get_label(uri):
        return class_label_map.get(uri, pretty(uri))
    for cls in sorted(changed_classes, key=lambda u: get_label(u).lower()):
        with st.expander(f"{get_label(cls)}"):
            added_edges_cls = [
                e for e in filter_non_subclassof(edges_new - edges_old) if e[0] == cls or e[2] == cls
            ]
            removed_edges_cls = [
                e for e in filter_non_subclassof(edges_old - edges_new) if e[0] == cls or e[2] == cls
            ]
            if added_edges_cls:
                st.write("**➕ New relations in v2:**")
                for a, p, b in added_edges_cls:
                    st.write(f"- {pretty(a)} --{pretty(p)}→ {pretty(b)}")
            if removed_edges_cls:
                st.write("**➖ Removed relations since v1:**")
                for a, p, b in removed_edges_cls:
                    st.write(f"- {pretty(a)} --{pretty(p)}→ {pretty(b)}")
            if not (added_edges_cls or removed_edges_cls):
                st.write("No object property relation changes for this class.")

# -------- Overview of New Classes -----------
with tabs[4]:
    st.subheader("Overview of New Classes")
    new_classes_info = []
    for _, row in cmp.loc[cmp["Status"] == "New"].iterrows():
        uri = URIRef(row["URI_new"])
        label = row["Label_new"]
        supers = [pretty(s) for s in g_new.objects(uri, RDFS.subClassOf)]
        subs = [
            pretty(sub) for sub in g_new.subjects(RDFS.subClassOf, uri)
            if (sub, RDF.type, OWL.Class) in g_new
        ]
        new_classes_info.append({
            "Label": label,
            "URI": row["URI_new"],
            "Superclasses": ", ".join(supers) if supers else "-",
            "Subclasses": ", ".join(subs) if subs else "-"
        })
    st.dataframe(pd.DataFrame(new_classes_info))
    show_mini = st.checkbox("Show mini-graphs of new classes (by domain)", value=True)
    if show_mini:
        df_new_indexed = df_new.set_index("URI")
        orphan_nodes = []
        new_nodes_with_super = []
        for u in new_nodes:
            u_uri = URIRef(u)
            superclasses = list(g_new.objects(u_uri, RDFS.subClassOf))
            uri_superclasses = [s for s in superclasses if isinstance(s, URIRef)]
            if uri_superclasses:
                new_nodes_with_super.append(u_uri)
            else:
                orphan_nodes.append(u_uri)

        # Group new classes with superclasses by domain
        doms_with_new = defaultdict(list)
        for u_uri in new_nodes_with_super:
            u_str = str(u_uri)
            try:
                dom = df_new_indexed.loc[u_str]["Domain"]
                doms_with_new[dom].append(u_uri)
            except KeyError:
                continue

        import matplotlib.pyplot as plt
        import networkx as nx
        import math

        for dom, dom_nodes in doms_with_new.items():
            st.markdown(f"#### {dom}")

            super_links = defaultdict(list)
            for cls in dom_nodes:
                for sup in g_new.objects(cls, RDFS.subClassOf):
                    if isinstance(sup, URIRef):
                        super_links[sup].append(cls)

            fig, ax = plt.subplots(figsize=(12, 10))

            # helper to keep duplicate labels distinct
            labels_seen = defaultdict(int)
            def unique_label(name: str) -> str:
                idx = labels_seen[name]
                labels_seen[name] += 1
                return name if idx == 0 else f"{name} ({idx+1})"

            for i, (sup_uri, subs) in enumerate(super_links.items()):
                num = len(subs)
                angle_step = 2 * math.pi / max(num, 2)  # ensure >0 when one child
                radius = 3 if num > 1 else 1.5
                center_x, center_y = 0, -i * 8

                cluster_graph = nx.DiGraph()
                cluster_graph.add_node(str(sup_uri), label=unique_label(pretty(sup_uri)), pos=(center_x, center_y))

                for j, sub_uri in enumerate(subs):
                    angle = j * angle_step
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    cluster_graph.add_node(
                        str(sub_uri),
                        label=unique_label(pretty(sub_uri)),
                        pos=(x, y)
                    )
                    cluster_graph.add_edge(str(sub_uri), str(sup_uri))

                pos    = nx.get_node_attributes(cluster_graph, "pos")
                labels = nx.get_node_attributes(cluster_graph, "label")

                nx.draw_networkx_nodes(cluster_graph, pos, ax=ax, node_color="#66BB66", node_size=1000)
                nx.draw_networkx_edges(cluster_graph, pos, ax=ax, arrows=True, arrowstyle='-|>', arrowsize=12)
                nx.draw_networkx_labels(cluster_graph, pos, labels=labels, font_size=9, font_weight="bold", ax=ax)

            ax.set_title(f"{dom} — Superclass", fontsize=14)
            ax.axis("off")
            st.pyplot(fig)

        # ------- Orphan list --------------------------------------------
        if orphan_nodes:
            st.markdown("#### 🧩 New classes without named superclass")
            fig, ax = plt.subplots(figsize=(10, max(1, len(orphan_nodes)) * 0.6))
            for i, uri in enumerate(orphan_nodes):
                label = df_new_indexed.loc[str(uri)]["Label"] if str(uri) in df_new_indexed.index else pretty(uri)
                ax.text(0.05, 1 - i * 0.08, label, fontsize=10)
            ax.axis("off")
            st.pyplot(fig)

# -------- Overview of New Relations -----------
with tabs[5]:
    st.subheader("Overview of New Relations")
    new_relations = list(edges_new - edges_old)
    if not new_relations:
        st.info("No new relations found in the new version.")
    else:
        uri2domain = df_new.set_index("URI")["Domain"].to_dict()
        rows = []
        for subj, pred, obj in new_relations:
            subj_str = str(subj)
            obj_str = str(obj)
            pred_str = str(pred)
            rows.append({
                "Domain (subj)": uri2domain.get(subj_str, "Other"),
                "Subject": pretty(subj),
                "Predicate": pretty(pred),
                "Object": pretty(obj),
                "Domain (obj)": uri2domain.get(obj_str, "Other"),
                "Subject URI": subj_str,
                "Object URI": obj_str
            })
        df_new_rel = pd.DataFrame(rows)
        st.dataframe(
            df_new_rel[["Domain (subj)", "Subject", "Predicate", "Object", "Domain (obj)"]],
            use_container_width=True,
            height=min(600, max(250, 30 * min(20, len(df_new_rel))))
        )
        dom_rel_counts = df_new_rel.groupby("Domain (subj)").size().sort_values(ascending=False)
        st.markdown("**New relations by subject domain:**")
        st.bar_chart(dom_rel_counts)
