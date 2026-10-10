package com.reg_iris.ingestion_service.demo.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.DateFormat;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(indexName = "regulatory_chunks")
public class RegulatoryChunkDocument {

    @Id
    private String id; // Matches paragraphId (e.g., DOC-1-P001)

    @Field(type = FieldType.Long)
    private Long documentId;

    @Field(type = FieldType.Keyword)
    private String fileName;

    @Field(type = FieldType.Keyword)
    private String regulator;

    @Field(type = FieldType.Keyword)
    private String jurisdiction;

    @Field(type = FieldType.Date, format = DateFormat.date)
    private LocalDate effectiveDate;

    @Field(type = FieldType.Keyword)
    private String category;

    @Field(type = FieldType.Keyword)
    private String version;

    @Field(type = FieldType.Integer)
    private Integer pageNumber;

    // Full-text analyzed field for BM-25 search
    @Field(type = FieldType.Text, analyzer = "standard")
    private String text;
}