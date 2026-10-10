package com.reg_iris.ingestion_service.demo.service;

import com.reg_iris.ingestion_service.demo.dto.DocumentChunk;
import lombok.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;

@Slf4j
@Service
public class EmbeddingWebhookService {

    private final WebClient webClient;

    public EmbeddingWebhookService(
            @Value("${fastapi.core-service.url:http://core-api-service:8000}") String fastApiBaseUrl) {
        this.webClient = WebClient.builder()
                .baseUrl(fastApiBaseUrl)
                .build();
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class EmbedChunksPayload {
        private Long docId;
        private String regulator;
        private List<DocumentChunk> chunks;
    }

    public void sendChunksToFastApi(Long docId, String regulator, List<DocumentChunk> chunks) {
        try {
            EmbedChunksPayload payload = new EmbedChunksPayload(docId, regulator, chunks);

            webClient.post()
                    .uri("/api/v1/internal/embed-chunks")
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(Void.class)
                    .doOnSuccess(v -> log.info("Dispatched {} chunks to FastAPI for doc ID {}", chunks.size(), docId))
                    .doOnError(e -> log.error("Failed to post chunks to FastAPI vector webhook: {}", e.getMessage()))
                    .subscribe();
        } catch (Exception e) {
            log.error("Error executing FastAPI embedding webhook", e);
        }
    }
}