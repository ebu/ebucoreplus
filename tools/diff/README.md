<p align="center">
  <img src="static/ebu_logo.svg" alt="EBU logo" width="160">
</p>

<h1 align="center">Ontology Diff Analyzer</h1>

<p align="center">
  A visual tool to compare two ontology versions and highlight class-level changes and relation differences.
</p>

---

## 🎬 Demo

<p align="center">
  <a href="https://ebu-oda.streamlit.app/" target="_blank">
    <img src="static/OntoDiffAnalyser.png" alt="Ontology Diff Analyzer Screenshot" width="800">
  </a>
</p>

<p align="center">
  👉 Try it live now: <strong><a href="https://ebu-oda.streamlit.app/">ebu-oda.streamlit.app</a></strong>
</p>

---

## ✨ Features

- 🆚 Compare two `.ttl` or `.owl` ontology versions
- 🕵️ Detect added, removed, and changed classes and properties
- 📊 Summarize changes visually with color-coded diff graphs

---

## 🚀 Run the Analyzer Locally

```bash
git clone https://github.com/ebu/ebucoreplus.git
cd ebucoreplus/tools/diff
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open your browser at [http://localhost:8501](http://localhost:8501)

---

## ☁️ Run it on Streamlit Cloud

No setup needed — just click and try:

👉 https://ebu-oda.streamlit.app/

---

## 📄 License

MIT License © European Broadcasting Union (EBU)

---

## 🙌 Acknowledgements

- [EBUCorePlus](https://tech.ebu.ch/metadata/ebucoreplus) — for the ontology baseline
- [rdflib](https://rdflib.readthedocs.io/) — RDF graph handling
- [streamlit](https://streamlit.io/) — for the UI framework

---

## 💬 Feedback

Have suggestions or want to contribute?  
Open an issue or pull request — feedback is always welcome!
