-- #############################################################################
-- ## Script:        activate_extensions.sql
-- ## Descripción:   Activa extensiones, schemas y tablas para grafo de conocimiento
-- ## Fecha:         2025-09-15
-- #############################################################################
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS fhirbase;
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = agens, public;

-- Crear esquema para el grafo si no existe
CREATE SCHEMA IF NOT EXISTS knowledge_graph;

-- Tablas para nodos y aristas (si no usas AGE puro)
CREATE TABLE IF NOT EXISTS knowledge_graph.nodes (
    node_uri TEXT PRIMARY KEY,
    node_type TEXT,
    name_nlp TEXT,
    description_nlp TEXT,
    properties_jsonb JSONB
);

CREATE TABLE IF NOT EXISTS knowledge_graph.edges (
    source_uri TEXT,
    target_uri TEXT,
    relationship_type TEXT,
    edge_uri TEXT,
    PRIMARY KEY (source_uri, target_uri, relationship_type)
);
