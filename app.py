"""
RAG Chatbot Flask Application
Modern web interface for university enrollment Q&A system
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import numpy as np
import psycopg2
import psycopg2.extras
import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import requests
import glob
from datetime import datetime
import secrets

# Load environment variables
load_dotenv('src/.env')

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Configuration
DATA_FOLDER = "data"
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'rag_chatbot'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}

db_connection_str = f"dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']} host={DB_CONFIG['host']} port={DB_CONFIG['port']}"

# Initialize embedding model globally (singleton pattern)
print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model loaded!")


# ========================
# UTILITY FUNCTIONS
# ========================

def calculate_embeddings(corpus: str) -> list[float]:
    """Calculate embeddings using Sentence Transformers"""
    embedding = embedding_model.encode(corpus, convert_to_numpy=True)
    return embedding.tolist()


def cosine_distance(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine distance between two vectors"""
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 1.0
    
    similarity = dot_product / (norm1 * norm2)
    return 1 - similarity


def similar_corpus(input_corpus: str, top_k: int = 5) -> list[tuple]:
    """Find similar corpus in database"""
    input_embedding = embedding_model.encode(input_corpus, convert_to_numpy=True).tolist()
    
    with psycopg2.connect(db_connection_str) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, corpus, embedding FROM embeddings")
            all_results = cur.fetchall()
            
            results_with_distance = []
            for row in all_results:
                id = row[0]
                corpus = row[1]
                embedding = row[2]
                
                # Parse embedding if it's a string (from pgvector or FLOAT8[])
                if isinstance(embedding, str):
                    if embedding.startswith('['):
                        embedding = [float(x) for x in embedding.strip('[]').split(',')]
                    elif embedding.startswith('{'):
                        embedding = [float(x) for x in embedding.strip('{}').split(',')]
                
                distance = cosine_distance(input_embedding, embedding)
                results_with_distance.append((distance, id, corpus))
            
            results_with_distance.sort(key=lambda x: x[0])
            return [(id, corpus, 1-distance) for distance, id, corpus in results_with_distance[:top_k]]


def generate_response(query: str, context: list[str]) -> dict:
    """Generate response using Groq LLM"""
    prompt = f"""Tu es un assistant spécialisé dans l'analyse de conversations universitaires.
Réponds UNIQUEMENT avec les informations du contexte. Si l'info n'est pas dans le contexte, dis-le clairement.

Contexte: {' '.join(context)}

Question: {query}

Réponse détaillée et structurée en français:"""
    
    try:
        start_time = time.time()
        
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "answer": result['choices'][0]['message']['content'],
            "time": round(elapsed, 2)
        }
        
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP Error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================
# DATABASE STATS FUNCTIONS
# ========================

def get_database_stats():
    """Get comprehensive database statistics"""
    try:
        with psycopg2.connect(db_connection_str) as conn:
            with conn.cursor() as cur:
                # Total records
                cur.execute("SELECT COUNT(*) FROM embeddings")
                total_records = cur.fetchone()[0]
                
                # Average corpus length
                cur.execute("SELECT AVG(LENGTH(corpus)) FROM embeddings")
                avg_length = cur.fetchone()[0]
                
                # Date range
                cur.execute("SELECT MIN(created_at), MAX(created_at) FROM embeddings")
                date_range = cur.fetchone()
                
                # Most recent entries
                cur.execute("SELECT corpus, created_at FROM embeddings ORDER BY created_at DESC LIMIT 5")
                recent = cur.fetchall()
                
                # Corpus length distribution
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN LENGTH(corpus) < 50 THEN 'Très court (<50)'
                            WHEN LENGTH(corpus) < 100 THEN 'Court (50-100)'
                            WHEN LENGTH(corpus) < 200 THEN 'Moyen (100-200)'
                            WHEN LENGTH(corpus) < 500 THEN 'Long (200-500)'
                            ELSE 'Très long (>500)'
                        END as length_category,
                        COUNT(*) as count
                    FROM embeddings
                    GROUP BY length_category
                    ORDER BY MIN(LENGTH(corpus))
                """)
                length_dist = cur.fetchall()
                
                return {
                    "success": True,
                    "total_records": total_records,
                    "avg_length": round(avg_length, 2) if avg_length else 0,
                    "date_range": {
                        "first": date_range[0].isoformat() if date_range[0] else None,
                        "last": date_range[1].isoformat() if date_range[1] else None
                    },
                    "recent_entries": [
                        {"text": r[0][:100] + "..." if len(r[0]) > 100 else r[0], 
                         "date": r[1].isoformat()}
                        for r in recent
                    ],
                    "length_distribution": [
                        {"category": cat, "count": cnt} 
                        for cat, cnt in length_dist
                    ]
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_data_files_info():
    """Get information about data files"""
    try:
        txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
        
        files_info = []
        total_lines = 0
        
        for file_path in txt_files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Count lines
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            lines = 0
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = len(f.readlines())
                    break
                except:
                    continue
            
            total_lines += lines
            
            files_info.append({
                "name": file_name,
                "size_kb": round(file_size / 1024, 2),
                "lines": lines
            })
        
        return {
            "success": True,
            "total_files": len(txt_files),
            "total_lines": total_lines,
            "files": sorted(files_info, key=lambda x: x['size_kb'], reverse=True)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_corpus(keyword: str, limit: int = 10):
    """Search corpus by keyword"""
    try:
        with psycopg2.connect(db_connection_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, corpus, created_at FROM embeddings WHERE corpus ILIKE %s LIMIT %s",
                    (f"%{keyword}%", limit)
                )
                results = cur.fetchall()
                
                return {
                    "success": True,
                    "results": [
                        {
                            "id": r[0],
                            "text": r[1],
                            "date": r[2].isoformat()
                        }
                        for r in results
                    ],
                    "count": len(results)
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================
# ROUTES
# ========================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')



@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.json
    query = data.get('question', data.get('query', ''))
    top_k = data.get('top_k', 5)
    
    if not query:
        return jsonify({"status": "error", "error": "Question is required"}), 400
    
    try:
        # Find similar corpus
        results = similar_corpus(query, top_k=top_k)
        
        # Extract context
        context = [corpus for _, corpus, _ in results]
        sources = [
            {
                "id": id,
                "text": corpus[:200] + "..." if len(corpus) > 200 else corpus,
                "relevance": round(relevance * 100, 1)
            }
            for id, corpus, relevance in results
        ]
        
        # Generate response
        response = generate_response(query, context)
        
        if response["success"]:
            # Track in session
            if 'chat_history' not in session:
                session['chat_history'] = []
            
            session['chat_history'].append({
                "query": query,
                "answer": response["answer"],
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify({
                "status": "success",
                "answer": response["answer"],
                "sources": sources,
                "response_time": response["time"],
                "sources_count": len(sources)
            })
        else:
            return jsonify({"status": "error", "error": response.get("error", "Unknown error")}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get database statistics"""
    try:
        with psycopg2.connect(db_connection_str) as conn:
            with conn.cursor() as cur:
                # Total records
                cur.execute("SELECT COUNT(*) FROM embeddings")
                total_records = cur.fetchone()[0]
                
                # Count unique files from data folder
                unique_files = len(glob.glob(os.path.join(DATA_FOLDER, "*.txt")))
                
                # Average corpus length
                cur.execute("SELECT AVG(LENGTH(corpus)) FROM embeddings")
                avg_length = cur.fetchone()[0] or 0
                
                # Length distribution for chart
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN LENGTH(corpus) < 50 THEN '0-50'
                            WHEN LENGTH(corpus) < 100 THEN '50-100'
                            WHEN LENGTH(corpus) < 200 THEN '100-200'
                            WHEN LENGTH(corpus) < 500 THEN '200-500'
                            ELSE '500+'
                        END as range,
                        COUNT(*) as count
                    FROM embeddings
                    GROUP BY range
                    ORDER BY MIN(LENGTH(corpus))
                """)
                length_dist = cur.fetchall()
                length_distribution = {cat: cnt for cat, cnt in length_dist}
                
                # File distribution - use data folder files
                file_distribution = {}
                txt_files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
                for i, file_path in enumerate(txt_files[:10], 1):
                    file_name = os.path.basename(file_path)
                    # Estimate records per file (total / number of files)
                    estimated_count = total_records // len(txt_files) if txt_files else 0
                    file_distribution[file_name] = estimated_count
                
                return jsonify({
                    "status": "success",
                    "stats": {
                        "total_records": total_records,
                        "unique_files": unique_files,
                        "avg_length": round(avg_length, 2),
                        "length_distribution": length_distribution,
                        "file_distribution": file_distribution
                    }
                })
    except Exception as e:
        print(f"ERROR in /api/stats: {str(e)}")  # Debug logging
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Search corpus by keyword"""
    data = request.json
    query = data.get('query', data.get('keyword', ''))
    limit = data.get('limit', 10)
    
    if not query:
        return jsonify({"status": "error", "error": "Query is required"}), 400
    
    result = search_corpus(query, limit)
    return jsonify(result)


@app.route('/api/history', methods=['GET'])
def history():
    """Get chat history"""
    chat_history = session.get('chat_history', [])
    return jsonify({
        "success": True,
        "history": chat_history[-10:],  # Last 10 conversations
        "count": len(chat_history)
    })


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    session['chat_history'] = []
    return jsonify({"success": True, "message": "History cleared"})


@app.route('/api/semantic-search', methods=['POST'])
def semantic_search():
    """Semantic search without generating response"""
    data = request.json
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    
    try:
        results = similar_corpus(query, top_k=top_k)
        
        return jsonify({
            "success": True,
            "results": [
                {
                    "id": id,
                    "text": corpus,
                    "relevance": round(relevance * 100, 1)
                }
                for id, corpus, relevance in results
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        with psycopg2.connect(db_connection_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "connected",
            "model": "loaded",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500



if __name__ == '__main__':
    print("=" * 80)
    print("🚀 RAG CHATBOT FLASK APPLICATION")
    print("=" * 80)
    print(f"📊 Database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
    print(f"🤖 Model: {GROQ_MODEL}")
    print(f"🧠 Embeddings: all-MiniLM-L6-v2")
    print("=" * 80)
    print("\n✅ Starting server on http://127.0.0.1:5000\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
