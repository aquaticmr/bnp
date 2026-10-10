package com.reg_iris.ingestion_service.demo.service;

import com.reg_iris.ingestion_service.demo.dto.DocumentChunk;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.jsoup.Jsoup;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

@Service
public class DocumentParsingService {

    private static final Pattern SECTION_PATTERN =
            Pattern.compile("^(Article\\s+\\d+|Section\\s+\\d+|CHAPTER\\s+[IVXLCDM]+|[0-9]+\\.[0-9]+).*$", Pattern.CASE_INSENSITIVE);

    public List<DocumentChunk> parseDocument(MultipartFile file, Long documentId, String regulator) {
        String filename = file.getOriginalFilename() != null ? file.getOriginalFilename().toLowerCase() : "";
        try {
            if (filename.endsWith(".pdf")) {
                return parsePdfPageByPage(file, documentId, regulator);
            } else if (filename.endsWith(".html") || filename.endsWith(".htm")) {
                return parseHtml(file, documentId, regulator);
            } else {
                return parsePlainText(file, documentId, regulator);
            }
        } catch (IOException e) {
            throw new RuntimeException("Document parsing error for: " + filename, e);
        }
    }

    private List<DocumentChunk> parsePdfPageByPage(MultipartFile file, Long documentId, String regulator) throws IOException {
        List<DocumentChunk> candidates = new ArrayList<>();

        try (PDDocument document = Loader.loadPDF(file.getBytes())) {
            int totalPages = document.getNumberOfPages();
            PDFTextStripper stripper = new PDFTextStripper();
            String currentSection = "General Provisions";

            for (int page = 1; page <= totalPages; page++) {
                stripper.setStartPage(page);
                stripper.setEndPage(page);
                String pageText = stripper.getText(document);

                String[] lines = pageText.split("\\r?\\n");
                StringBuilder buffer = new StringBuilder();

                for (String line : lines) {
                    String trimmed = line.trim();
                    if (trimmed.isEmpty()) {
                        if (buffer.length() > 0) {
                            addChunkCandidate(candidates, documentId, currentSection, page, buffer.toString(), regulator);
                            buffer.setLength(0);
                        }
                    } else if (SECTION_PATTERN.matcher(trimmed).matches()) {
                        if (buffer.length() > 0) {
                            addChunkCandidate(candidates, documentId, currentSection, page, buffer.toString(), regulator);
                            buffer.setLength(0);
                        }
                        currentSection = trimmed;
                    } else {
                        buffer.append(trimmed).append(" ");
                    }
                }
                if (buffer.length() > 0) {
                    addChunkCandidate(candidates, documentId, currentSection, page, buffer.toString(), regulator);
                }
            }
        }
        return linkAndFilterChunks(candidates);
    }

    private List<DocumentChunk> parseHtml(MultipartFile file, Long documentId, String regulator) throws IOException {
        org.jsoup.nodes.Document doc = Jsoup.parse(file.getInputStream(), "UTF-8", "");
        List<DocumentChunk> candidates = new ArrayList<>();
        String currentSection = "General Provisions";
        int pageCounter = 1;
        int wordCount = 0;

        for (org.jsoup.nodes.Element element : doc.body().children()) {
            if (element.tagName().matches("h[1-6]")) {
                currentSection = element.text().trim();
            } else if (element.tagName().equals("p") && !element.text().isBlank()) {
                String text = element.text().trim();
                wordCount += text.split("\\s+").length;
                if (wordCount > 400) {
                    pageCounter++;
                    wordCount = 0;
                }
                addChunkCandidate(candidates, documentId, currentSection, pageCounter, text, regulator);
            }
        }
        return linkAndFilterChunks(candidates);
    }

    private List<DocumentChunk> parsePlainText(MultipartFile file, Long documentId, String regulator) throws IOException {
        String fullText = new String(file.getBytes(), StandardCharsets.UTF_8);
        String[] paragraphs = fullText.split("\\r?\\n\\r?\\n");
        List<DocumentChunk> candidates = new ArrayList<>();
        int pageCounter = 1;
        int wordCount = 0;

        for (String para : paragraphs) {
            String trimmed = para.replaceAll("\\s+", " ").trim();
            if (trimmed.length() < 20) continue;

            wordCount += trimmed.split("\\s+").length;
            if (wordCount > 400) {
                pageCounter++;
                wordCount = 0;
            }
            addChunkCandidate(candidates, documentId, "General Provisions", pageCounter, trimmed, regulator);
        }
        return linkAndFilterChunks(candidates);
    }

    private void addChunkCandidate(List<DocumentChunk> list, Long docId, String section, int page, String text, String regulator) {
        String clean = text.replaceAll("\\s+", " ").trim();
        if (clean.length() < 20) return;

        // Contamination scrub check
        String lowerClean = clean.toLowerCase();
        if ("EMIR".equalsIgnoreCase(regulator) && lowerClean.contains("dodd-frank")) {
            return;
        }
        if ("MiFID II".equalsIgnoreCase(regulator) && lowerClean.contains("cftc")) {
            return;
        }

        list.add(DocumentChunk.builder()
                .documentId(docId)
                .parentSectionId(section)
                .pageNumber(page)
                .text(clean)
                .build());
    }

    private List<DocumentChunk> linkAndFilterChunks(List<DocumentChunk> chunks) {
        int index = 1;
        for (DocumentChunk chunk : chunks) {
            chunk.setChunkId(String.format("DOC-%d-P%03d", chunk.getDocumentId(), index++));
        }

        for (int i = 0; i < chunks.size(); i++) {
            DocumentChunk current = chunks.get(i);
            current.setPrevChunkId(i > 0 ? chunks.get(i - 1).getChunkId() : null);
            current.setNextChunkId(i < chunks.size() - 1 ? chunks.get(i + 1).getChunkId() : null);
        }
        return chunks;
    }
}