<p align="center">
  <img src="static/ebu_logo.svg" alt="EBU logo" width="160">
</p>

<h1 align="center">Ontology Explorer</h1>

<p align="center">
  A user-friendly tool to explore RDF/OWL ontologies like <strong>EBUCorePlus</strong> using fuzzy search, semantic graph visualization, and domain-aware class navigation.
</p>

---

## 🎬 Live Demo

<p align="center">
  <img src="static/demo.gif" alt="Ontology Explorer UI Demo" width="800">
</p>

---

## ✨ Features

- 🔍 Fuzzy search with autocomplete
- 🧭 Class selection by functional domain
- 🧠 Interactive semantic graph using `pyvis`
- 🔗 Displays subclasses, superclasses, restrictions, reverse links, and SKOS info

---

## 🚀 Getting Started

```bash
git clone https://github.com/yourusername/OntologyExplorer.git
cd OntologyExplorer
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run main.py
```

Then open your browser at [http://localhost:8501](http://localhost:8501)

---

## ☁️ Run it on Streamlit Cloud

...
---

## 📄 License

MIT License © Alexandre Rouxel

---

## 🙌 Acknowledgements

- [EBU](https://tech.ebu.ch/metadata/ebucoreplus) — for the EBUCorePlus ontology
- [rdflib](https://rdflib.readthedocs.io/) — for semantic RDF parsing
- [pyvis](https://pyvis.readthedocs.io/) — for graph visualization
- [streamlit](https://streamlit.io/) — for building this web UI

---

## 💬 Feedback

Found a bug? Want to contribute?  
Open an issue or pull request — feedback is always welcome!
