package com.reg_iris.ingestion_service.demo.model;
import com.reg_iris.ingestion_service.demo.dto.DocumentStatus;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.ZonedDateTime;

@Entity
@Table(name = "regulatory_documents")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RegulatoryDocument {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "document_id")
    private Long documentId;

    @Column(name = "family_id", nullable = false)
    private String familyId; // e.g., "MIFID_II", "EMIR", "DODD_FRANK"

    @Column(name = "file_name", nullable = false)
    private String fileName;

    @Column(name = "sha256_hash", nullable = false, unique = true)
    private String sha256Hash;

    private String regulator;
    private String jurisdiction;
    private String category;
    private String version; // e.g., "v1.0", "v2.0"

    // Bitemporal & Metadata verification
    @Column(name = "published_at")
    private LocalDate publishedAt;

    @Column(name = "effective_from")
    private LocalDate effectiveFrom;

    @Column(name = "effective_to")
    private LocalDate effectiveTo;

    @Enumerated(EnumType.STRING)
    private DocumentStatus status;

    @Column(name = "has_metadata_conflict")
    private boolean hasMetadataConflict;

    @Column(name = "parent_doc_id")
    private Long parentDocId;

    @Column(name = "storage_path", nullable = false)
    private String storagePath;

    @Column(name = "upload_timestamp")
    private ZonedDateTime uploadTimestamp;
}