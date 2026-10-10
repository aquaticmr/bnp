package com.reg_iris.ingestion_service.demo.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.ZonedDateTime;

@Entity
@Table(name = "doc_metadata")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DocumentMetadata {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "document_id")
    private Long documentId;

    @Column(name = "file_name", nullable = false)
    private String fileName;

    @Column(name = "storage_path")
    private String storagePath;

    @Column(name = "regulator", nullable = false)
    private String regulator;

    @Column(name = "jurisdiction")
    private String jurisdiction;

    @JsonFormat(pattern = "dd-MM-yy")
    @Column(name = "effective_date")
    private LocalDate effectiveDate;

    @Column(name = "category")
    private String category;

    @Column(name = "version")
    private String version;

    @Column(name = "upload_timestamp")
    private ZonedDateTime uploadTimestamp;

    @Column(name = "parent_doc_id")
    private Long parentDocId;
}