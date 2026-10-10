package com.reg_iris.ingestion_service.demo.service;

import com.reg_iris.ingestion_service.demo.dto.DocumentChunk;
import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.AllMiniLmL6V2EmbeddingModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.chroma.ChromaEmbeddingStore;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class ChromaDBService {

    // Keep batches small: one huge embedAll()/addAll() call is what trips
    // the HTTP timeout and memory limits on large PDFs.
    private static final int BATCH_SIZE = 64;

    private final EmbeddingStore<TextSegment> embeddingStore;
    private final EmbeddingModel embeddingModel;

    public ChromaDBService(
            @Value("${chromadb.url}") String chromaUrl,
            @Value("${chromadb.collection}") String collectionName) {

        // The default HTTP timeout in langchain4j-chroma is short (a few seconds).
        this.embeddingStore = ChromaEmbeddingStore.builder()
                .baseUrl(chromaUrl)
                .collectionName(collectionName)
                .timeout(Duration.ofSeconds(60))
                .build();

        // Local ONNX model, 384-dimensional vectors.
        // The Chroma collection must only ever receive vectors from this same model.
        this.embeddingModel = new AllMiniLmL6V2EmbeddingModel();
    }

    public void storeEmbeddings(List<DocumentChunk> chunks, DocumentMetadata docMetadata) {
        if (chunks == null || chunks.isEmpty()) {
            log.warn("No chunks to embed for DOC ID: {}", docMetadata.getDocumentId());
            return;
        }

        // 1. Map chunks to TextSegments. Metadata is String->String only,
        //    which is what langchain4j 0.30.0 expects and Chroma accepts.
        List<TextSegment> segments = chunks.stream().map(chunk -> {
            Map<String, String> meta = new HashMap<>();
            putIfPresent(meta, "chunk_id", chunk.getChunkId());
            putIfPresent(meta, "parent_section_id", chunk.getParentSectionId());
            putIfPresent(meta, "document_id", String.valueOf(docMetadata.getDocumentId()));
            putIfPresent(meta, "file_name", docMetadata.getFileName());
            putIfPresent(meta, "regulator", docMetadata.getRegulator());
            putIfPresent(meta, "page_number", String.valueOf(chunk.getPageNumber()));
            return TextSegment.from(chunk.getText(), Metadata.from(meta));
        }).toList();

        // 2 + 3. Embed and store in batches.
        int stored = 0;
        try {
            for (int i = 0; i < segments.size(); i += BATCH_SIZE) {
                List<TextSegment> batch = segments.subList(i, Math.min(i + BATCH_SIZE, segments.size()));
                List<Embedding> embeddings = embeddingModel.embedAll(batch).content();
                embeddingStore.addAll(embeddings, batch);
                stored += batch.size();
            }
        } catch (RuntimeException e) {
            log.error("Embedding/Chroma failure for DOC ID {} after {} of {} chunks: {}",
                    docMetadata.getDocumentId(), stored, segments.size(), e.toString(), e);
            throw e;
        }

        log.info("Successfully stored {} vector embeddings in ChromaDB for DOC ID: {}",
                stored, docMetadata.getDocumentId());
    }

    private static void putIfPresent(Map<String, String> map, String key, String value) {
        if (value != null) {
            map.put(key, value);
        }
    }
}