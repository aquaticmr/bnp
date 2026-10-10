package com.reg_iris.ingestion_service.demo.controller;

import com.reg_iris.ingestion_service.demo.dto.DocumentUploadRequest;
import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import com.reg_iris.ingestion_service.demo.repository.DocumentMetadataRepository;
import com.reg_iris.ingestion_service.demo.service.DocumentStorageService;
import com.reg_iris.ingestion_service.demo.orchestrator.IngestionOrchestratorService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api/v1/ingest")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class IngestionController {

    private final IngestionOrchestratorService orchestratorService;
    private final DocumentMetadataRepository docRepository;
    private final DocumentStorageService storageService;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentMetadata> uploadDocument(
            @RequestPart("file") MultipartFile file,
            @ModelAttribute DocumentUploadRequest request) {
        DocumentMetadata ingested =
                orchestratorService.processDocument(file, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(ingested);
    }

    @GetMapping("/versions/{regulator}")
    public ResponseEntity<List<DocumentMetadata>> getVersionAuditTrail(@PathVariable String regulator) {
        return ResponseEntity.ok(docRepository.findAllByRegulatorOrderByDocumentIdAsc(regulator));
    }

    @GetMapping("/documents/{docId}/raw")
    public ResponseEntity<byte[]> getRawDocumentBinary(@PathVariable Long docId) throws IOException {
        DocumentMetadata doc = docRepository.findById(docId)
                .orElseThrow(() -> new IllegalArgumentException("Document not found with ID: " + docId));

        byte[] binary = storageService.loadFileBytes(doc.getRegulator(), doc.getVersion(), doc.getFileName());

        MediaType mediaType = MediaType.APPLICATION_OCTET_STREAM;
        if (doc.getFileName().toLowerCase().endsWith(".pdf")) {
            mediaType = MediaType.APPLICATION_PDF;
        } else if (doc.getFileName().toLowerCase().endsWith(".html")) {
            mediaType = MediaType.TEXT_HTML;
        }

        return ResponseEntity.ok()
                .contentType(mediaType)
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + doc.getFileName() + "\"")
                .body(binary);
    }
}