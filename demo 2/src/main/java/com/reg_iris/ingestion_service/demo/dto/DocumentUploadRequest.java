package com.reg_iris.ingestion_service.demo.dto;

import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class DocumentUploadRequest {
    private String regulator;
    private String jurisdiction;
    private String category;

    @DateTimeFormat(pattern = "dd-MM-yy")
    private LocalDate effectiveDate;

    private String version; // Optional manual override (e.g., "v1.1", "v2.0")
}