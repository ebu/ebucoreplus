```markdown
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

- 🔍 Fuzzy search with autocomplete (`streamlit-searchbox`)
- 🧭 Class selection by domain (e.g., Editorial, Distribution, Participation…)
- 🧱 Visual semantic graph using `pyvis`
- 🔗 Displays: subclasses, superclasses, restrictions, reverse properties
- 📦 Loads `.ttl` and `.owl` ontologies (RDF/XML, Turtle)
- ⚡ Automatically expands graph when a new class is selected

---

## 📁 Project Structure

```

OntologyExplorer/
├── main.py                   # Main Streamlit app
├── ontology\_helpers.py      # RDF helper functions
├── graph\_helpers.py         # Graph building logic
├── config.py                 # Class groupings & colors
├── static/
│   ├── demo.gif              # UI animation for README/Streamlit Cloud
│   ├── OntoExplorer.png      # Static screenshot
│   └── ebu\_logo.svg         # EBU branding
├── requirements.txt          # Dependencies
└── README.md

````

---

## 🚀 Get Started - local installation 

```bash
git clone https://github.com/yourusername/OntologyExplorer.git
cd OntologyExplorer
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run main.py
````

Then open your browser to `http://localhost:8501`

---

## ☁️ Streamlit Cloud

You can deploy directly to Streamlit Cloud:

1. Push the repo to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your repo, set `main.py` as the app entry point
4. Upload your ontology `.ttl` file in the interface

⚠️ Make sure `demo.gif` and `ebu_logo.svg` are in `static/` folder.


---

## 📄 License

MIT License © 

---

## 💬 Feedback

Feature ideas, bugs, or contributions? Open a GitHub issue

