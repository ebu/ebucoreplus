from rdflib import Graph, RDF, RDFS, OWL, URIRef
import pandas as pd

# ----------- helper functions ----------
def pretty(uri: URIRef) -> str:
    s = str(uri)
    return s.split("#")[-1] if "#" in s else s.split("/")[-1]

def build_class_stats(g: Graph) -> pd.DataFrame:
    class_info = {}
    all_classes = {
        cls for cls in g.subjects(RDF.type, OWL.Class)
        if isinstance(cls, URIRef)
    }
    for cls in all_classes:
        label = next(
            (str(l) for l in g.objects(cls, RDFS.label)
             if getattr(l, "language", None) == "en"),
            pretty(cls),
        )
        class_info[cls] = dict(
            label=label, subclasses=0, obj_props=0, relations=0, uri=str(cls)
        )

    for sub, _, sup in g.triples((None, RDFS.subClassOf, None)):
        if sup in class_info and (sub, RDF.type, OWL.Class) in g:
            class_info[sup]["subclasses"] += 1
            class_info[sup]["relations"] += 1
            class_info[sub]["relations"] += 1

    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        for cls in g.objects(prop, RDFS.domain):
            if cls in class_info:
                class_info[cls]["obj_props"] += 1
                class_info[cls]["relations"] += 1
        for cls in g.objects(prop, RDFS.range):
            if cls in class_info:
                class_info[cls]["obj_props"] += 1
                class_info[cls]["relations"] += 1

    for cls in class_info:
        for rest in g.objects(cls, RDFS.subClassOf):
            if (rest, RDF.type, OWL.Restriction) in g:
                for p in [OWL.someValuesFrom, OWL.allValuesFrom, OWL.hasValue]:
                    for tgt in g.objects(rest, p):
                        if tgt in class_info:
                            class_info[cls]["relations"] += 1
                            class_info[tgt]["relations"] += 1

    return pd.DataFrame([
        dict(
            Label=info["label"],
            URI=info["uri"],
            Subclasses=info["subclasses"],
            ObjectProperties=info["obj_props"],
            TotalRelations=info["relations"]
        )
        for info in class_info.values()
    ])

def extract_edges(g: Graph, class_set: set[URIRef]) -> set[tuple]:
    edges = set()
    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        for d in g.objects(prop, RDFS.domain):
            for r in g.objects(prop, RDFS.range):
                if d in class_set and r in class_set:
                    edges.add((d, prop, r))
    for sub, _, sup in g.triples((None, RDFS.subClassOf, None)):
        if sub in class_set and sup in class_set:
            edges.add((sub, URIRef("subClassOf"), sup))
    for cls in class_set:
        for rest in g.objects(cls, RDFS.subClassOf):
            if (rest, RDF.type, OWL.Restriction) in g:
                prop = next(g.objects(rest, OWL.onProperty), None)
                if prop:
                    for p in [OWL.someValuesFrom, OWL.allValuesFrom, OWL.hasValue]:
                        for tgt in g.objects(rest, p):
                            if tgt in class_set:
                                edges.add((cls, prop, tgt))
    return edges


def class_nice_view(g, class_uri):
    """
    Return a human-readable Markdown block for a class, showing:
    - URI
    - English label
    - English description
    - Superclasses (as prefixed names)
    """
    prefix_map = {
        "http://www.ebu.ch/metadata/ontologies/ebucoreplus#": "ec:",
        "http://purl.org/dc/terms/": "dcterms:",
        "http://www.w3.org/2004/02/skos/core#": "skos:",
        "http://www.w3.org/2002/07/owl#": "owl:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    }
    def prefixed(uri):
        s = str(uri)
        for ns, prefix in prefix_map.items():
            if s.startswith(ns):
                return s.replace(ns, prefix)
        return f"<{s}>"
    c = URIRef(class_uri)
    lines = []
    # URI
    lines.append(f"**URI:** [{class_uri}]({class_uri})")
    # English label
    label = next((l for l in g.objects(c, RDFS.label) if getattr(l, 'language', None) == 'en'), None)
    if label:
        lines.append(f"**Label:** {label}")
    # English description
    desc = next((d for d in g.objects(c, URIRef('http://purl.org/dc/terms/description')) if getattr(d, 'language', None) == 'en'), None)
    if desc:
        lines.append(f"**Description:** {desc}")
    # Superclasses
    supers = [s for s in g.objects(c, RDFS.subClassOf) if isinstance(s, URIRef)]
    if supers:
        lines.append(f"**Superclass{'es' if len(supers)>1 else ''}:** " + ", ".join(prefixed(s) for s in supers))
    return "\n\n".join(lines)


def compare_object_properties(g_new, g_old, class_uri):
    """
    Return sets of object property URIs where class_uri is in domain or range,
    and show which were added or removed.
    """
    def obj_props(graph):
        props = set()
        c = URIRef(class_uri)
        for p in graph.subjects(RDF.type, OWL.ObjectProperty):
            if (p, RDFS.domain, c) in graph or (p, RDFS.range, c) in graph:
                props.add(p)
        return props

    new_props = obj_props(g_new)
    old_props = obj_props(g_old)
    added = new_props - old_props
    removed = old_props - new_props
    return added, removed
