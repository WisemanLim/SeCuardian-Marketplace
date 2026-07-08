import client from "./client";

export interface RagCollection {
  id: number;
  tenant_id: string;
  name: string;
  description: string;
  sensitivity: "general" | "sensitive";
  embedding_dim: number;
  embedding_version: string;
}

export interface RagDocument {
  id: number;
  collection_id: number;
  title: string;
  source: string;
  chunks: number;
}

export interface RagSearchHit {
  chunk_id: number;
  document_id: number;
  text: string;
  dense_rank: number | null;
  bm25_rank: number | null;
  dense_score: number;
  bm25_score: number;
  rrf_score: number;
}

export async function listCollections(): Promise<RagCollection[]> {
  const { data } = await client.get<{ collections: RagCollection[] }>("/rag/collections");
  return data.collections ?? [];
}

export async function createCollection(body: {
  name: string;
  description?: string;
  sensitivity?: "general" | "sensitive";
}): Promise<RagCollection> {
  const { data } = await client.post<RagCollection>("/rag/collections", body);
  return data;
}

export async function listDocuments(collectionId: number): Promise<RagDocument[]> {
  const { data } = await client.get<{ documents: RagDocument[] }>(`/rag/collections/${collectionId}/documents`);
  return data.documents ?? [];
}

export async function ingestDocument(
  collectionId: number,
  body: { title?: string; source?: string; text: string },
): Promise<RagDocument> {
  const { data } = await client.post<RagDocument>(`/rag/collections/${collectionId}/documents`, body);
  return data;
}

export async function search(collectionId: number, query: string, topK?: number): Promise<RagSearchHit[]> {
  const { data } = await client.post<{ hits: RagSearchHit[] }>(`/rag/collections/${collectionId}/search`, {
    query, top_k: topK,
  });
  return data.hits ?? [];
}
