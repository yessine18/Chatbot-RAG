import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
from pathlib import Path
from sentence_transformers import SentenceTransformer
import PyPDF2
import glob

# Charger les variables d'environnement
load_dotenv()

# Initialiser le modèle d'embeddings
print("🧠 Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded!")


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = []
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
            
            return "\n".join(text_content)
    except Exception as e:
        print(f"❌ Error reading PDF {pdf_path}: {e}")
        return None


def load_data_from_folder(data_folder="data"):
    """Load text from .txt and .pdf files in data folder"""
    documents = []
    
    # Load .txt files
    txt_files = glob.glob(os.path.join(data_folder, "*.txt"))
    for txt_file in txt_files:
        try:
            # Essayer différents encodages
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(txt_file, 'r', encoding=encoding) as f:
                        content = f.read().strip()
                        if content:
                            documents.append({
                                'file': os.path.basename(txt_file),
                                'content': content,
                                'type': 'txt'
                            })
                        break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️  Error reading {txt_file}: {e}")
    
    # Load .pdf files
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    for pdf_file in pdf_files:
        content = extract_text_from_pdf(pdf_file)
        if content:
            documents.append({
                'file': os.path.basename(pdf_file),
                'content': content,
                'type': 'pdf'
            })
    
    return documents

def create_database():
    """
    Crée la base de données rag_chatbot avec support PDF et TXT
    """
    try:
        # Connexion au serveur PostgreSQL (base postgres par défaut)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            database='postgres'
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Vérifier si la base existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'rag_chatbot'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('rag_chatbot')))
            print("✅ Database 'rag_chatbot' created!")
        else:
            print("ℹ️  Database 'rag_chatbot' already exists.")
        
        cursor.close()
        conn.close()
        
        # Se connecter à rag_chatbot pour créer les tables
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            database='rag_chatbot'
        )
        cursor = conn.cursor()
        
        # Activer pgvector
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("✅ pgvector extension enabled!")
        
        # Créer la table embeddings
        cursor.execute("""
            DROP TABLE IF EXISTS embeddings;
            CREATE TABLE embeddings (
                id SERIAL PRIMARY KEY,
                corpus TEXT NOT NULL,
                embedding VECTOR(384),
                file_name VARCHAR(255),
                file_type VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'embeddings' created!")
        
        # Créer l'index HNSW pour recherche rapide
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS embeddings_embedding_idx 
            ON embeddings USING hnsw (embedding vector_cosine_ops)
        """)
        print("✅ HNSW index created!")
        
        conn.commit()
        
        # Charger les données depuis data/
        print("\n📂 Loading data from data/ folder...")
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        documents = load_data_from_folder(data_path)
        
        print(f"📊 Found {len(documents)} documents:")
        txt_count = sum(1 for d in documents if d['type'] == 'txt')
        pdf_count = sum(1 for d in documents if d['type'] == 'pdf')
        print(f"   - {txt_count} .txt files")
        print(f"   - {pdf_count} .pdf files")
        
        # Insérer les embeddings
        print("\n🔄 Generating embeddings and inserting into database...")
        total_inserted = 0
        
        for doc in documents:
            # Diviser en chunks si nécessaire
            content = doc['content']
            chunks = [content[i:i+500] for i in range(0, len(content), 500)]
            
            for chunk in chunks:
                if chunk.strip():
                    # Générer embedding
                    embedding = model.encode(chunk).tolist()
                    
                    # Insérer dans la DB
                    cursor.execute(
                        """
                        INSERT INTO embeddings (corpus, embedding, file_name, file_type)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (chunk, embedding, doc['file'], doc['type'])
                    )
                    total_inserted += 1
        
        conn.commit()
        print(f"✅ Inserted {total_inserted} embeddings into database!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Test database connection and show stats"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            database='rag_chatbot'
        )
        cursor = conn.cursor()
        
        # Stats
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT file_name) FROM embeddings")
        files = cursor.fetchone()[0]
        
        cursor.execute("SELECT file_type, COUNT(*) FROM embeddings GROUP BY file_type")
        by_type = cursor.fetchall()
        
        print("\n📊 Database Statistics:")
        print(f"   Total embeddings: {total}")
        print(f"   Unique files: {files}")
        print(f"   By type:")
        for ftype, count in by_type:
            print(f"     - {ftype.upper()}: {count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 RAG CHATBOT - DATABASE SETUP WITH PDF SUPPORT")
    print("=" * 60)
    
    if create_database():
        print("\n🔍 Testing connection...")
        test_connection()
    
    print("\n" + "=" * 60)
    print("✨ Setup complete!")
    print("=" * 60)
