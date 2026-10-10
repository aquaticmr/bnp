package com.reg_iris.ingestion_service.demo.service;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.UUID;

@Service
public class MinioStorageService {

    private final MinioClient minioClient;
    private final String bucketName;

    // Inject properties and initialize the Minio Client
    public MinioStorageService(
            @Value("${minio.url}") String url,
            @Value("${minio.access.key}") String accessKey,
            @Value("${minio.secret.key}") String secretKey,
            @Value("${minio.bucket.name}") String bucketName) {

        this.minioClient = MinioClient.builder()
                .endpoint(url)
                .credentials(accessKey, secretKey)
                .build();
        this.bucketName = bucketName;

        // Ensure the bucket exists on application startup
        try {
            boolean found = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
            if (!found) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
            }
        } catch (Exception e) {
            throw new RuntimeException("Error initializing MinIO bucket during startup", e);
        }
    }

    public String uploadFile(MultipartFile file) {
        try (InputStream inputStream = file.getInputStream()) {
            // Generate a unique filename to prevent overwriting
            String objectName = UUID.randomUUID() + "-" + file.getOriginalFilename();

            // Upload the file stream to MinIO
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucketName)
                            .object(objectName)
                            .stream(inputStream, file.getSize(), -1)
                            .contentType(file.getContentType())
                            .build());

            // Return the storage path reference
            return bucketName + "/" + objectName;

        } catch (Exception e) {
            throw new RuntimeException("Failed to upload document to MinIO", e);
        }
    }
}


