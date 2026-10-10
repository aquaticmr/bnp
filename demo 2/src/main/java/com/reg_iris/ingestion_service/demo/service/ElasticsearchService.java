package com.reg_iris.ingestion_service.demo.service;

import com.reg_iris.ingestion_service.demo.dto.DocumentChunk;
import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.DateFormat;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ElasticsearchService {

    private final ElasticsearchOperations elasticsearchOperations;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Document(indexName = "regulatory_clauses")
    public static class ClauseIndexItem {
        @Id
        private String chunkId;

        @Field(type = FieldType.Long)
        private Long documentId;

        @Field(type = FieldType.Keyword)
        private String fileName;

        @Field(type = FieldType.Keyword)
        private String regulator;

        @Field(type = FieldType.Keyword)
        private String jurisdiction;

        @Field(type = FieldType.Keyword)
        private String category;

        @Field(type = FieldType.Keyword)
        private String version;

        @Field(type = FieldType.Keyword)
        private String parentSectionId;

        @Field(type = FieldType.Keyword)
        private String prevChunkId;

        @Field(type = FieldType.Keyword)
        private String nextChunkId;

        @Field(type = FieldType.Integer)
        private int pageNumber;

        @Field(type = FieldType.Date, format = DateFormat.date)
        private LocalDate effectiveDate;

        @Field(type = FieldType.Text, analyzer = "standard")
        private String text;
    }

    public void indexDocumentClauses(List<DocumentChunk> chunks, DocumentMetadata doc) {
        List<ClauseIndexItem> indexItems = chunks.stream().map(c -> ClauseIndexItem.builder()
                .chunkId(c.getChunkId())
                .documentId(doc.getDocumentId())
                .fileName(doc.getFileName())
                .regulator(doc.getRegulator())
                .jurisdiction(doc.getJurisdiction())
                .category(doc.getCategory())
                .version(doc.getVersion())
                .parentSectionId(c.getParentSectionId())
                .prevChunkId(c.getPrevChunkId())
                .nextChunkId(c.getNextChunkId())
                .pageNumber(c.getPageNumber())
                .effectiveDate(doc.getEffectiveDate())
                .text(c.getText())
                .build()
        ).collect(Collectors.toList());

        elasticsearchOperations.save(indexItems);
        log.info("Indexed {} clauses into 'regulatory_clauses' for Doc ID: {}", indexItems.size(), doc.getDocumentId());
    }
}