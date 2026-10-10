package com.reg_iris.ingestion_service.demo.repository;

import com.reg_iris.ingestion_service.demo.model.DocumentMetadata;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface DocumentMetadataRepository extends JpaRepository<DocumentMetadata, Long> {

    Optional<DocumentMetadata> findTopByRegulatorOrderByDocumentIdDesc(String regulator);

    List<DocumentMetadata> findAllByRegulatorOrderByDocumentIdAsc(String regulator);

    Optional<DocumentMetadata> findTopByFileNameOrderByDocumentIdDesc(String fileName);
}