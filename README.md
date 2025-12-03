# 🤖 RAG Chatbot - Système de Questions-Réponses Intelligent

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-enabled-orange.svg)](https://github.com/pgvector/pgvector)

Un système de chatbot intelligent utilisant **Retrieval-Augmented Generation (RAG)** avec **pgvector** pour la recherche vectorielle et **Groq LLM** pour la génération de réponses.

---

## 📋 Table des matières

- [Vue d'ensemble](#-vue-densemble)
- [Architecture](#-architecture)
- [Technologies utilisées](#-technologies-utilisées)
- [Structure du projet](#-structure-du-projet)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Scripts Python](#-scripts-python)
- [API Flask](#-api-flask)
- [Recherche vectorielle](#-recherche-vectorielle-pgvector)
- [Interface Web](#-interface-web)
- [Utilisation](#-utilisation)
- [Déploiement](#-déploiement)

---

## 🎯 Vue d'ensemble

Ce projet implémente un **chatbot RAG (Retrieval-Augmented Generation)** capable de répondre aux questions sur l'inscription universitaire en se basant sur :
- **41 fichiers `.txt`** : Conversations historiques sur les inscriptions
- **Fichiers PDF** : Documentation officielle (ex: `accueil_ubs.pdf`)

### Fonctionnalités principales

✅ **Recherche vectorielle ultra-rapide** avec pgvector  
✅ **Support multi-formats** : TXT + PDF  
✅ **Interface web interactive** avec statistiques temps réel  
✅ **API REST complète** pour intégration externe  
✅ **Historique des conversations** avec sources citées  
✅ **Gestion multi-encodage** (UTF-8, Latin-1, CP1252)

---

## 🏗️ Architecture

```
┌──────────────┐
│  User Query  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Flask API (app.py)              │
│  ┌─────────────────────────────────┐   │
│  │  1. Sentence Transformer         │   │
│  │     (all-MiniLM-L6-v2)          │   │
│  │     → Embedding (384 dims)       │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   PostgreSQL + pgvector Extension       │
│  ┌─────────────────────────────────┐   │
│  │  2. Cosine Similarity Search     │   │
│  │     embedding <=> query_vector   │   │
│  │     → Top-K documents (sources)  │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Groq API (LLM)                  │
│  ┌─────────────────────────────────┐   │
│  │  3. Generate Response            │   │
│  │     Model: llama-3.1-8b-instant  │   │
│  │     Context: Top-K sources       │   │
│  │     → Final Answer               │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────┐
│   Response to User   │
│  - Answer            │
│  - Sources (cited)   │
│  - Response time     │
└──────────────────────┘
```

---

## 🛠️ Technologies utilisées

### Backend
| Technologie | Version | Usage |
|------------|---------|-------|
| **Python** | 3.9+ | Langage principal |
| **Flask** | 3.0.0 | API REST framework |
| **PostgreSQL** | 16+ | Base de données |
| **pgvector** | Latest | Extension pour recherche vectorielle |
| **psycopg2** | 2.9.11 | Connecteur PostgreSQL |

### Intelligence Artificielle
| Modèle | Dimensions | Usage |
|--------|-----------|-------|
| **Sentence Transformers** | 384 | Génération d'embeddings (all-MiniLM-L6-v2) |
| **Groq LLM** | - | Génération de réponses (llama-3.1-8b-instant) |

### Frontend
| Technologie | Usage |
|------------|-------|
| **HTML5/CSS3** | Interface utilisateur |
| **JavaScript (Vanilla)** | Logique frontend |
| **Chart.js** | Visualisation des statistiques |
| **Marked.js** | Rendu Markdown |
| **Font Awesome** | Icônes |

### Traitement de documents
| Bibliothèque | Usage |
|-------------|-------|
| **PyPDF2** | Extraction de texte depuis PDF |
| **pandas** | Manipulation de données |
| **numpy** | Calculs numériques |

---

## 📁 Structure du projet

```
Chatbot-RAG/
│
├── 📄 app.py                    # Flask API principale (498 lignes)
├── 📄 requirements.txt          # Dépendances Python
├── 📄 .env.example              # Template de configuration
├── 📄 README.md                 # Documentation (ce fichier)
│
├── 📂 src/                      # Scripts utilitaires
│   ├── create_db.py             # Création DB + import données
│   ├── extract_pdf.py           # Extraction PDF → TXT
│   └── create_database.sql      # Schema SQL (legacy)
│
├── 📂 data/                     # Données sources
│   ├── *.txt                    # 41 conversations (UTF-8/Latin-1)
│   └── *.pdf                    # Documents PDF (ex: accueil_ubs.pdf)
│
├── 📂 templates/                # Templates HTML
│   ├── index.html               # Interface principale
│   └── test.html                # Page de test API
│
├── 📂 static/                   # Assets frontend
│   ├── css/
│   │   └── style.css            # Styles personnalisés
│   └── js/
│       └── app.js               # Logique frontend (493 lignes)
│
└── 📂 notebook/                 # Prototypes Jupyter
    ├── prototypage.ipynb        # RAG prototype
    └── multi_agent_brain_tumor.ipynb  # Système multi-agents (Option C)
```

---

## 🚀 Installation

### Prérequis

- **Python 3.9+**
- **PostgreSQL 16+** avec extension **pgvector**
- **Groq API Key** (gratuit sur [console.groq.com](https://console.groq.com))

### Étape 1 : Télécharger le projet

```bash
# Si vous avez cloné depuis GitHub
git clone <votre-repo-url>
cd Chatbot-RAG

# Ou naviguez directement vers le dossier du projet
cd "C:\Users\USER\Desktop\ChatBot Rag\Chatbot-RAG"
```

### Étape 2 : Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Étape 3 : Installer les dépendances

```bash
pip install -r requirements.txt
```

### Étape 4 : Installer pgvector dans PostgreSQL

```sql
-- Se connecter à PostgreSQL en tant que superuser
CREATE EXTENSION IF NOT EXISTS vector;
```

### Étape 5 : Configurer les variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer .env avec vos valeurs
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Contenu de `.env` :**
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_NAME=rag_chatbot

GROQ_API_KEY=votre_clé_groq_ici
```

### Étape 6 : Créer la base de données et importer les données

```bash
cd src
python create_db.py
```

**Sortie attendue :**
```
🧠 Loading embedding model...
✅ Model loaded!
============================================================
📊 Found 43 documents:
   - 41 .txt files
   - 2 .pdf files
✅ Inserted 305 embeddings into database!
```

---

## ⚙️ Configuration

### Variables d'environnement (.env)

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `DB_HOST` | Hôte PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |
| `DB_USER` | Utilisateur DB | `postgres` |
| `DB_PASSWORD` | Mot de passe DB | `your_password_here` |
| `DB_NAME` | Nom de la base | `rag_chatbot` |
| `GROQ_API_KEY` | Clé API Groq | **OBLIGATOIRE** |
| `GROQ_MODEL` | Modèle LLM | `llama-3.1-8b-instant` |
| `EMBEDDING_MODEL` | Modèle embeddings | `all-MiniLM-L6-v2` |
| `TOP_K` | Nombre de sources | `5` |
| `MAX_TOKENS` | Tokens max réponse | `500` |
| `TEMPERATURE` | Créativité LLM | `0.7` |

---

## 📜 Scripts Python

### 1️⃣ `app.py` - API Flask principale

**Lignes de code :** 498  
**Rôle :** Serveur Flask avec API REST complète

#### Fonctions clés :

| Fonction | Description | Technologie |
|----------|-------------|-------------|
| `similar_corpus(query, top_k)` | Recherche vectorielle | **pgvector** (cosine similarity) |
| `generate_response(question, sources)` | Génération de réponse | **Groq LLM** |
| `parse_postgres_array(pg_array)` | Parse embeddings | Gestion format `[...]` et `{...}` |

#### Endpoints API :

| Endpoint | Méthode | Description | Retour |
|----------|---------|-------------|--------|
| `/` | GET | Page d'accueil | HTML |
| `/test` | GET | Page test API | HTML |
| `/api/chat` | POST | Poser une question | JSON (answer, sources, time) |
| `/api/stats` | GET | Statistiques DB | JSON (records, files, avg_length) |
| `/api/health` | GET | Health check | JSON (status, db, model) |
| `/api/history` | GET | Historique session | JSON (messages[]) |
| `/api/clear-history` | POST | Effacer historique | JSON (success) |
| `/api/semantic-search` | POST | Recherche pure | JSON (results[]) |

#### Architecture de recherche :

```python
# 1. Génération de l'embedding (384 dimensions)
query_embedding = model.encode(question).tolist()

# 2. Recherche pgvector (cosine similarity)
query = """
    SELECT id, corpus, 
           1 - (embedding <=> %s::vector) as similarity
    FROM embeddings
    ORDER BY embedding <=> %s::vector
    LIMIT %s
"""
# Opérateur <=> : distance cosinus optimisée par HNSW index

# 3. Génération de réponse avec contexte
response = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "Tu es un assistant..."},
        {"role": "user", "content": f"Question: {question}\nContext: {sources}"}
    ]
)
```

---

### 2️⃣ `src/create_db.py` - Création et peuplement de la base

**Rôle :** Initialise PostgreSQL, active pgvector, charge les données

#### Étapes du script :

```python
1. create_database()
   ├── CREATE DATABASE rag_chatbot
   ├── CREATE EXTENSION vector
   ├── CREATE TABLE embeddings (
   │       id SERIAL PRIMARY KEY,
   │       corpus TEXT,
   │       embedding VECTOR(384),  # ← pgvector type
   │       file_name VARCHAR(255),
   │       file_type VARCHAR(10),
   │       created_at TIMESTAMP
   │   )
   └── CREATE INDEX USING hnsw (embedding vector_cosine_ops)

2. load_data_from_folder()
   ├── Charge .txt (multi-encodage : UTF-8, Latin-1, CP1252)
   └── Charge .pdf (PyPDF2.PdfReader)

3. Insert embeddings
   ├── Découpe en chunks (500 caractères)
   ├── Génère embedding pour chaque chunk
   └── INSERT INTO embeddings (corpus, embedding, file_name, file_type)
```

#### Gestion multi-encodage :

```python
# Essai automatique de plusieurs encodages
for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
    try:
        with open(txt_file, 'r', encoding=encoding) as f:
            content = f.read()
            break  # Premier encodage qui fonctionne
    except UnicodeDecodeError:
        continue
```

---

### 3️⃣ `src/extract_pdf.py` - Extraction de texte PDF

**Rôle :** Convertit les PDF en fichiers `.txt`

```python
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text_content = []
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n".join(text_content)
```

**Utilisation :**
```bash
cd src
python extract_pdf.py
```

---

## 🔌 API Flask

### Exemple de requête `/api/chat`

**Request :**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Comment valider mon inscription ?",
    "top_k": 5
  }'
```

**Response :**
```json
{
  "status": "success",
  "answer": "Pour valider votre inscription, vous devez...",
  "sources": [
    {
      "id": 1047,
      "text": "h: inscription administrative oui",
      "relevance": 52.8
    },
    {
      "id": 258,
      "text": "h: un souci avec une inscription",
      "relevance": 47.9
    }
  ],
  "sources_count": 2,
  "response_time": 0.76
}
```

### Statistiques `/api/stats`

**Response :**
```json
{
  "status": "success",
  "stats": {
    "total_records": 305,
    "unique_files": 43,
    "avg_length": 187,
    "files_distribution": {
      "TXT": 41,
      "PDF": 2
    }
  }
}
```

---

## 🔍 Recherche vectorielle (pgvector)

### ❓ Pourquoi pgvector au lieu de FLOAT[] ?

| Aspect | pgvector | FLOAT[] classique |
|--------|----------|-------------------|
| **Performance** | ✅ Indexation HNSW/IVFFlat | ❌ Scan séquentiel complet |
| **Scalabilité** | ✅ Millions de vecteurs | ❌ Ralentit avec >10k |
| **Opérateurs** | ✅ `<=>` (cosine), `<->` (L2) | ❌ Calcul manuel en Python |
| **SQL natif** | ✅ `ORDER BY embedding <=> query` | ❌ Requêtes complexes |
| **Mémoire** | ✅ Optimisé (compression) | ❌ Stockage brut |

### Exemple de requête pgvector :

```sql
-- Recherche des 5 documents les plus similaires
SELECT 
    id, 
    corpus, 
    1 - (embedding <=> '[0.123, -0.456, ...]'::vector) AS similarity
FROM embeddings
ORDER BY embedding <=> '[0.123, -0.456, ...]'::vector
LIMIT 5;
```

### Index HNSW (Hierarchical Navigable Small World)

```sql
CREATE INDEX embeddings_embedding_idx 
ON embeddings 
USING hnsw (embedding vector_cosine_ops);
```

**Avantages :**
- ⚡ Recherche en **O(log N)** au lieu de O(N)
- 🎯 Précision : ~95-99% des résultats exacts
- 📈 Scalable jusqu'à des millions de vecteurs

---

## 🎨 Interface Web

### Page principale (`/`)

**Fonctionnalités :**
- 💬 **Chat interactif** : Pose de questions avec historique
- 📊 **Dashboard** : 4 cartes de statistiques
- 📈 **Graphique** : Distribution des fichiers (Chart.js)
- 🔍 **Recherche sémantique** : Tab dédiée
- 📜 **Historique** : Conversations sauvegardées en session

**Technologies :**
- HTML5 + CSS3 (Gradient purple-blue)
- JavaScript Vanilla (Fetch API)
- Chart.js (Visualisation)
- Marked.js (Markdown rendering)

### Page de test (`/test`)

Interface simplifiée pour tester directement les endpoints API.

---

## 📊 Données et résultats

### Base de données actuelle

| Métrique | Valeur |
|----------|--------|
| **Total embeddings** | 305 |
| **Fichiers .txt** | 41 (134 chunks) |
| **Fichiers .pdf** | 2 (171 chunks) |
| **Dimensions** | 384 (all-MiniLM-L6-v2) |
| **Index** | HNSW (cosine similarity) |

### Performance

| Opération | Temps moyen |
|-----------|-------------|
| Génération embedding | ~50ms |
| Recherche pgvector (top-5) | ~10ms |
| Génération LLM (Groq) | ~500-800ms |
| **Total (end-to-end)** | **~0.6-1s** |

---

## 🚀 Utilisation

### Démarrer le serveur Flask

```bash
python app.py
```

**Sortie :**
```
================================================================================
🚀 RAG CHATBOT FLASK APPLICATION
================================================================================
📊 Database: rag_chatbot@localhost
🤖 Model: llama-3.1-8b-instant
🧠 Embeddings: all-MiniLM-L6-v2
================================================================================

✅ Starting server on http://127.0.0.1:5000
```

### Accéder à l'interface

- **Interface principale :** http://localhost:5000
- **Test API :** http://localhost:5000/test
- **Health check :** http://localhost:5000/api/health

### Exemples de questions

**Pour les fichiers .txt (inscriptions) :**
- "Comment faire mon inscription administrative ?"
- "Quels documents sont nécessaires ?"
- "Où se trouve le bureau des inscriptions ?"

**Pour le PDF (accueil_ubs.pdf) :**
- "Qu'est-ce que l'UBS ?"
- "Quels sont les services de l'université ?"
- "Comment contacter l'accueil ?"

---

## 📦 Déploiement

### Variables d'environnement production

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<générer-une-clé-sécurisée>
```

### Générer une clé secrète :

```python
import secrets
print(secrets.token_hex(32))
```

### Hébergement recommandé

- **Backend :** Heroku, Railway, Render
- **Base de données :** Railway PostgreSQL (pgvector natif), Supabase
- **Frontend :** Vercel, Netlify (si séparé)

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 🐛 Dépannage

### Erreur : `ModuleNotFoundError: No module named 'psycopg2'`

```bash
pip install psycopg2-binary
```

### Erreur : `extension "vector" does not exist`

```sql
-- En tant que superuser PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
```

### Encodage des fichiers .txt

Le script gère automatiquement UTF-8, Latin-1, CP1252. Si erreur, convertir manuellement :

```bash
iconv -f ISO-8859-1 -t UTF-8 fichier.txt > fichier_utf8.txt
```

### Clé Groq invalide

Vérifier sur [console.groq.com](https://console.groq.com) que la clé est active.

---

## 📞 Support

Pour toute question ou assistance, consultez la documentation ci-dessus ou vérifiez les logs de l'application.

---

## Features

- Retrieval-Augmented Generation for enhanced responses
- Context-aware conversations
- Easy-to-use interface

## Getting Started

### Prerequisites

- Python 3.8+
- Required dependencies (to be listed in requirements.txt)

### Installation

```bash
# Clone the repository
git clone git@github.com:yessine18/Chatbot-RAG.git
cd Chatbot-RAG

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Run the chatbot
python main.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
