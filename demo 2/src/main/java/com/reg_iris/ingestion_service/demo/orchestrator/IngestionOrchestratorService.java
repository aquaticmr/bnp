package com.reg_iris.ingestion_service.demo.orchestrator;


import com.reg_iris.ingestion_service.demo.dto.DocumentChunk;
import com.reg_iris.ingestion_service.demo.dto.DocumentUploadRequest;
import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import com.reg_iris.ingestion_service.demo.service.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import java.util.List;

@Service
@RequiredArgsConstructor
public class IngestionOrchestratorService {

    private final MinioStorageService minioStorageService;
    private final MetadataVersioningService metadataVersioningService;
    private final DocumentParsingService documentParsingService;
    private final ElasticsearchService elasticsearchService;
    private final ChromaDBService chromaDBService;

    @Transactional
    public DocumentMetadata processDocument(MultipartFile file, DocumentUploadRequest request) {
        // 1. Upload raw file to MinIO
        String storagePath = minioStorageService.uploadFile(file);

        // 2. Metadata & Versioning in PostgreSQL
        DocumentMetadata metadata = metadataVersioningService.trackAndVersionDocument(
                file.getOriginalFilename(), storagePath, request);

        // 3. Page-Aware Parsing & Chunking
        List<DocumentChunk> chunks =
                documentParsingService.parseDocument(
                        file,
                        metadata.getDocumentId(),
                        metadata.getRegulator()
                );
        // 4. Index in Elasticsearch (BM-25)
        elasticsearchService.indexDocumentClauses(chunks, metadata);

        // 5. Store Embeddings in ChromaDB (Semantic Search)
        chromaDBService.storeEmbeddings(chunks, metadata);

        return metadata;
    }
}