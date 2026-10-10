package com.reg_iris.ingestion_service.demo.service;


import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;

@Service
public class DocumentStorageService {

    @Value("${storage.root-path:/data/storage}")
    private String rootStoragePath;

    public Path resolvePath(String regulator, String version, String fileName) {
        String sanitizedRegulator = regulator.replaceAll("[^a-zA-Z0-9_-]", "_");
        return Paths.get(rootStoragePath, sanitizedRegulator, version, fileName);
    }

    public void saveFile(MultipartFile file, String regulator, String version) {
        try {
            Path targetPath = resolvePath(regulator, version, file.getOriginalFilename());
            Files.createDirectories(targetPath.getParent());
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            throw new RuntimeException("Could not save binary to storage volume", e);
        }
    }

    public byte[] loadFileBytes(String regulator, String version, String fileName) throws IOException {
        Path path = resolvePath(regulator, version, fileName);
        return Files.readAllBytes(path);
    }
}