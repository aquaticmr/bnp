package com.reg_iris.ingestion_service.demo.service;


import com.reg_iris.ingestion_service.demo.dto.DocumentUploadRequest;
import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import com.reg_iris.ingestion_service.demo.repository.DocumentMetadataRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.time.ZonedDateTime;

@Service
@RequiredArgsConstructor
public class MetadataVersioningService {

    private final DocumentMetadataRepository repository;

    public DocumentMetadata trackAndVersionDocument(String fileName, String storagePath, DocumentUploadRequest request) {
        DocumentMetadata metadata = new DocumentMetadata();
        metadata.setFileName(fileName);
        metadata.setRegulator(request.getRegulator());
        metadata.setJurisdiction(request.getJurisdiction());
        metadata.setEffectiveDate(request.getEffectiveDate());
        metadata.setCategory(request.getCategory());
        metadata.setUploadTimestamp(ZonedDateTime.now());
        metadata.setStoragePath(storagePath);

        // Versioning Logic
        repository.findTopByFileNameOrderByDocumentIdDesc(fileName).ifPresentOrElse(
                parentDoc -> {
                    metadata.setParentDocId(parentDoc.getDocumentId());
                    metadata.setVersion(incrementVersion(parentDoc.getVersion()));
                },
                () -> {
                    metadata.setParentDocId(null);
                    metadata.setVersion("v1.0");
                }
        );

        return repository.save(metadata);
    }

    private String incrementVersion(String currentVersion) {
        if (currentVersion == null || !currentVersion.startsWith("v")) return "v1.0";
        try {
            double vNum = Double.parseDouble(currentVersion.replace("v", ""));
            return "v" + String.format("%.1f", vNum + 1.0); // e.g., v1.0 -> v2.0
        } catch (NumberFormatException e) {
            return currentVersion + "-updated";
        }
    }
}