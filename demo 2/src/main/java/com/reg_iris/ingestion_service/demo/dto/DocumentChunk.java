package com.reg_iris.ingestion_service.demo.dto;

import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentChunk {
    private String chunkId;           // e.g., "DOC-001-P001"
    private Long documentId;
    private String parentSectionId;   // e.g., "Article 4 - Transaction Reporting"
    private String prevChunkId;       // Backward link for context expansion
    private String nextChunkId;       // Forward link for context expansion
    private int pageNumber;           // Citation starting page
    private String text;
}