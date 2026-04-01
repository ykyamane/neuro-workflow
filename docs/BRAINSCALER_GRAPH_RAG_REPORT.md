# BrainScaler Hybrid Graph-RAG System: Features, Principles, and Architecture

## 1. Overview

This BrainScaler setup is a **hybrid graph-RAG system**. It uses:

- **Postgres** for uploaded papers metadata and file references.
- **Neo4j** for the knowledge graph (Documents, Chunks, Entities, Relationships, embeddings).
- **Graph builder stack** (`graph_with_ontology`): ingests PDFs from Postgres, parses them, and builds/updates the graph in Neo4j.
- **Frontend stack** (`brainscaler_frontend`): chat UI, RAG over Neo4j, and graph visualization.

The pipeline turns each paper into a **structured graph** (document → chunks → entities) plus **embeddings**, and the chat uses **vector search + graph expansion** to answer questions.

---

## 2. Per-Document Graph Structure (Why You See Separate Subgraphs)

Each uploaded paper is processed **independently** and forms its **own connected component** in Neo4j:

- **`Document` node** – One per paper (labels contain `Document`), with metadata (e.g. `title`, `file_path`).
- **`Chunk` nodes** – The document text is split into chunks; each chunk has `text`, `index`, and an **embedding** for RAG. Relationships: `(:Chunk)-[:FROM_DOCUMENT]->(:Document)` and `(:Chunk)-[:NEXT_CHUNK]->(:Chunk)` for order.
- **Entity nodes** – Ontology-driven types (e.g. `Person`, `Concept`, `Organization`) created by an LLM extractor. Relationships: `(:Entity)-[:FROM_CHUNK]->(:Chunk)` and various domain relations (e.g. `AFFILIATED_WITH`, `RELATED_TO`, `USES`, `CITES`) **only between entities from the same document**.

There is **no cross-document linking** (no entity resolution, no cross-paper relations). So each paper’s Document+Chunk+Entity structure is a **separate “mini-graph”**. In Neo4j Browser this appears as **three disconnected clusters** (one per paper) when you run something like `MATCH (n)-[r]->(m) RETURN n,r,m LIMIT ...`. **This is by design**, not a bug.

---

## 3. Why Different Queries Show Different “Numbers of Documents”

- **`MATCH (n) RETURN n LIMIT 1000`** – Returns an arbitrary subset of nodes; the Browser graph view also only draws a subset. So you may see only **2** Document nodes even though **3** exist.
- **Focused document–chunk query** – e.g. `MATCH (doc)-[r]-(c) WHERE ... Document ... Chunk ... RETURN doc, r, c` returns **all** Documents that have Chunks (all three papers), so you see three hubs.
- **Document–chunk–entity path query** – e.g. `MATCH path = (doc)-[:FROM_DOCUMENT*0..2]-(chunk)-[:FROM_CHUNK]-(entity) ... RETURN path LIMIT 300` only returns paths where a Chunk has a `FROM_CHUNK` link to an Entity. If one document has fewer such links, it may not appear in the first 300 paths, and the visualization looks like a dense “cloud” of Chunks+Entities rather than three clear Document hubs.

---

## 4. RAG Component: Embeddings and Vector Store

The system has a full **RAG pipeline** on top of the graph:

- **Chunk embeddings** – Each `:Chunk` node has an `embedding` property (e.g. **1536-dimensional**). A Neo4j **vector index** (`text_embeddings` on `(:Chunk.embedding)`) is used for similarity search.
- **Question embedding** – When you ask a question in the chat (Graph DB mode), the frontend embeds the question (e.g. with `OpenAIEmbeddings(...)`) and queries the `text_embeddings` index via `db.index.vector.queryNodes` to get the most similar chunks.
- **RAG + graph retrieval** – The retriever (e.g. **VectorCypherRetriever**) uses a Cypher query (from `config.json`) that starts from those top-k chunks (`WITH node AS chunk`), then walks 1–3 hops of relationships (e.g. `FROM_CHUNK`, other typed relations) to collect **related entities and relationships**, and builds a string context: `=== text ===` (chunk texts) and `=== kg_rels ===` (formatted relationships).
- **LLM answer** – A GraphRAG instance takes `query_text` and that `context` and produces `result.answer`, which the frontend returns as the chat reply.

So the system is **hybrid**: **RAG** (embeddings + vector index + similarity search) plus **graph** (structured entities/relations and Cypher traversals to enrich RAG context). A **fallback** path exists: if GraphRAG returns the boilerplate “context does not contain any information about …”, the frontend runs a direct text search over `Chunk.text` in Neo4j, concatenates matching chunk texts as context, and calls the base LLM again so the user still gets an answer from the document text.

---

## 5. Ontologies: What They Are and How They’re Used

**Ontologies** here are the `.ttl` files in `graph_with_ontology/build_graph/ontologies` (e.g. `efeatures.ttl`). They are **OWL/RDF ontologies** from external neuroscience work (Blue Brain Project, Neuroshapes, etc.) and define **classes** (node types) and sometimes relationship types, with labels and descriptions.

**How they’re used:**

- For each ontology, the pipeline builds a **schema** via `getSchemaFromOnto(ontology_path)` (allowed node types and properties).
- In Phase 2, for each document and ontology, an **LLM-based entity extractor** (`LLMEntityRelationExtractor`) sees the **chunk text** and the **schema**, and outputs nodes (with a type from the schema, e.g. Person, Concept) and relationships between them (e.g. AFFILIATED_WITH). The code also normalizes the schema (adds `label`/`description` properties and sets `additional_properties=False`) so the model is constrained but has useful fields.

**Crucially:** ontologies in this repo are **fixed** – the system **reads** them and never writes or updates them when new papers are ingested. New papers only create new **instances** (nodes and edges) **under** that schema; they do **not** change the ontologies themselves.

---

## 6. Design Trade-offs of This Architecture

**Advantages:**

- **Semantic retrieval** (embeddings) plus **explicit structure** (graph).
- **Per-document subgraphs** make it clear which entities and chunks belong to which paper.
- **Explainable answers** – the graph view shows what was retrieved.
- Ontology-constrained extraction keeps entity types and relationships consistent across documents.

**Disadvantages / current limitations:**

- **No cross-document entity resolution** – e.g. “Kenji Doya” in paper 1 and paper 2 are separate nodes; there is no global “same person” linkage yet.
- **Complexity** – embedding model, vector index config, and graph schema must stay aligned (e.g. 1536 vs 500 dimension issues).
- **Ontology and extraction quality** – if ontologies or LLM extraction are off, the graph is noisy and can mislead RAG.
- **Neo4j Browser display limits** – for large graphs, only a subset of nodes is drawn; use focused queries and higher “max nodes” settings to see all documents.

---

## 7. Summary

The system builds **one local knowledge graph per paper** (document → chunks → entities → relations) and stores **embeddings** for each chunk. At query time it uses **embeddings** to find relevant chunks (RAG), then **graph connections** around those chunks to enrich context, and the **LLM** answers from that combined context. A **fallback** path uses direct Neo4j text search over chunk text when GraphRAG returns an empty-context message. That is why you see three distinct subgraphs in Neo4j (one per paper), the chat answering questions about any of the three papers, and a graph visualization tied to the chat answers.
