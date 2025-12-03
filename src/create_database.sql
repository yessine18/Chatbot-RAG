-- Vérifier si la base de données existe
-- SELECT 1 FROM pg_database WHERE datname = 'rag_chatbot';

-- Création de la base de données rag_chatbot
CREATE DATABASE rag_chatbot
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
