import datetime
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import DocumentMetadataRecord, RegulatoryAlertRecord
from app.db.session import SessionLocal, init_db
from app.search.chroma_client import chroma_client
from app.search.elasticsearch_client import elasticsearch_client
from app.search.embeddings import embedding_service

logger = logging.getLogger(__name__)

INITIAL_CLAUSES: List[Dict[str, Any]] = [
    {
        "chunkId": "EMIR-DOC1-P001",
        "documentId": 1,
        "fileName": "EMIR_Technical_Standards_v1.0.pdf",
        "regulator": "EMIR",
        "jurisdiction": "EU",
        "category": "TRANSACTION_REPORTING",
        "version": "v1.0",
        "parentSectionId": "Article 9 - Reporting Obligation",
        "pageNumber": 14,
        "effectiveDate": "2024-04-29",
        "text": "Counterparties and CCPs shall ensure that the details of any derivative contract they have concluded and of any modification or termination of the contract are reported to a trade repository registered in accordance with Article 55 or recognised in accordance with Article 77 no later than the working day following the conclusion, counterparties must be uniquely identified by an active 20-character ISO 17442 Legal Entity Identifier (LEI).",
    },
    {
        "chunkId": "EMIR-DOC1-P002",
        "documentId": 1,
        "fileName": "EMIR_Technical_Standards_v1.0.pdf",
        "regulator": "EMIR",
        "jurisdiction": "EU",
        "category": "TRANSACTION_REPORTING",
        "version": "v1.0",
        "parentSectionId": "Article 9(3) - Contract Characteristics",
        "pageNumber": 16,
        "effectiveDate": "2024-04-29",
        "text": "The maturity date of the contract shall be strictly posterior to the execution date. The price, quantity, and notional amount must be populated with verified positive numerical values unless explicit negative yield conventions apply to fixed income benchmark derivatives.",
    },
    {
        "chunkId": "EMIR-DOC2-P001",
        "documentId": 2,
        "fileName": "EMIR_Technical_Standards_v2.0.pdf",
        "regulator": "EMIR",
        "jurisdiction": "EU",
        "category": "TRANSACTION_REPORTING",
        "version": "v2.0",
        "parentSectionId": "Article 9 - Refit Reporting Validation",
        "pageNumber": 5,
        "effectiveDate": "2026-01-15",
        "text": "Under EMIR Refit standards, all transaction reports must incorporate the Unique Trade Identifier (UTI) and Unique Product Identifier (UPI). Validation rules require that counterparty LEIs must be validated against the Global Legal Entity Identifier Foundation (GLEIF) database prior to trade submission.",
    },
    {
        "chunkId": "MIFID-DOC3-P001",
        "documentId": 3,
        "fileName": "MiFID_II_RTS_22_Reporting_Guide.pdf",
        "regulator": "MiFID II",
        "jurisdiction": "EU",
        "category": "TRADE_TRANSPARENCY",
        "version": "v1.2",
        "parentSectionId": "Article 15 - Transaction Price Fields",
        "pageNumber": 22,
        "effectiveDate": "2024-01-01",
        "text": "Investment firms reporting transactions under Article 26 of Regulation (EU) No 600/2014 shall state the price of the transaction in the currency in which the transaction was executed. Traded prices must be strictly positive numerical values. Where the transaction is executed on a trading venue, Field 36 (Venue) must contain the four-letter Market Identifier Code (MIC) under ISO 10383.",
    },
    {
        "chunkId": "MIFID-DOC3-P002",
        "documentId": 3,
        "fileName": "MiFID_II_RTS_22_Reporting_Guide.pdf",
        "regulator": "MiFID II",
        "jurisdiction": "EU",
        "category": "TRADE_TRANSPARENCY",
        "version": "v1.2",
        "parentSectionId": "RTS 25 - Clock Synchronization & Timestamp Granularity",
        "pageNumber": 38,
        "effectiveDate": "2024-01-01",
        "text": "Operators of trading venues and their members shall ensure their clocks are synchronized to UTC with maximum divergence thresholds. For high frequency and algorithmic trading systems, execution timestamps must be captured at microsecond granularity conforming to ISO 8601 UTC standard.",
    },
    {
        "chunkId": "CFTC-DOC4-P001",
        "documentId": 4,
        "fileName": "Dodd_Frank_CFTC_Part_43_Guide.pdf",
        "regulator": "Dodd-Frank",
        "jurisdiction": "US",
        "category": "SWAP_DATA_RECORDKEEPING",
        "version": "v1.0",
        "parentSectionId": "Part 43 - Real-Time Public Reporting",
        "pageNumber": 12,
        "effectiveDate": "2024-06-30",
        "text": "CFTC Part 43 governs real-time public reporting of swap transaction and pricing data. Reporting entities must publicly disseminate swap transaction data as soon as technologically practicable following execution. The transaction quantity and notional volume must be strictly greater than zero.",
    },
    {
        "chunkId": "CFTC-DOC4-P002",
        "documentId": 4,
        "fileName": "Dodd_Frank_CFTC_Part_43_Guide.pdf",
        "regulator": "Dodd-Frank",
        "jurisdiction": "US",
        "category": "SWAP_DATA_RECORDKEEPING",
        "version": "v1.0",
        "parentSectionId": "Part 45 - Swap Data Recordkeeping § 45.3",
        "pageNumber": 27,
        "effectiveDate": "2024-06-30",
        "text": "Swap counterparties must transmit primary economic terms (PET) data to a registered Swap Data Repository (SDR). Permitted asset classes are restricted to Rates, Credit, Equity, FX, and Commodity. The legal identity of reporting entities and non-reporting counterparties must be designated via Legal Entity Identifiers.",
    },
    {
        "chunkId": "FCA-DOC5-P001",
        "documentId": 5,
        "fileName": "FCA_SUP_17_Transaction_Reporting.pdf",
        "regulator": "FCA",
        "jurisdiction": "UK",
        "category": "MARKET_ABUSE",
        "version": "v1.1",
        "parentSectionId": "SUP 17 Annex 1 - Reporting Standards",
        "pageNumber": 8,
        "effectiveDate": "2024-03-31",
        "text": "FCA authorized investment firms must submit accurate transaction reports to the FCA Market Data Processor (MDP). Currency codes must be populated using valid 3-letter ISO 4217 alphabetic currency codes. Reports containing invalid currency codes or unregistered trading counterparties are automatically rejected.",
    },
]


def seed_database_and_indices():
    """
    Initializes database tables, loads seed document metadata,
    and indexes initial regulatory clauses into Elasticsearch and ChromaDB.
    """
    init_db()
    db: Session = SessionLocal()

    try:
        # 1. Seed document metadata if empty
        existing_doc_count = db.query(DocumentMetadataRecord).count()
        if existing_doc_count == 0:
            logger.info("Seeding initial document metadata records...")
            records = [
                DocumentMetadataRecord(
                    document_id=1,
                    file_name="EMIR_Technical_Standards_v1.0.pdf",
                    storage_path="reg-iris-docs/EMIR_Technical_Standards_v1.0.pdf",
                    regulator="EMIR",
                    jurisdiction="EU",
                    effective_date=datetime.date(2024, 4, 29),
                    category="TRANSACTION_REPORTING",
                    version="v1.0",
                    parent_doc_id=None,
                ),
                DocumentMetadataRecord(
                    document_id=2,
                    file_name="EMIR_Technical_Standards_v2.0.pdf",
                    storage_path="reg-iris-docs/EMIR_Technical_Standards_v2.0.pdf",
                    regulator="EMIR",
                    jurisdiction="EU",
                    effective_date=datetime.date(2026, 1, 15),
                    category="TRANSACTION_REPORTING",
                    version="v2.0",
                    parent_doc_id=1,
                ),
                DocumentMetadataRecord(
                    document_id=3,
                    file_name="MiFID_II_RTS_22_Reporting_Guide.pdf",
                    storage_path="reg-iris-docs/MiFID_II_RTS_22_Reporting_Guide.pdf",
                    regulator="MiFID II",
                    jurisdiction="EU",
                    effective_date=datetime.date(2024, 1, 1),
                    category="TRADE_TRANSPARENCY",
                    version="v1.2",
                    parent_doc_id=None,
                ),
                DocumentMetadataRecord(
                    document_id=4,
                    file_name="Dodd_Frank_CFTC_Part_43_Guide.pdf",
                    storage_path="reg-iris-docs/Dodd_Frank_CFTC_Part_43_Guide.pdf",
                    regulator="Dodd-Frank",
                    jurisdiction="US",
                    effective_date=datetime.date(2024, 6, 30),
                    category="SWAP_DATA_RECORDKEEPING",
                    version="v1.0",
                    parent_doc_id=None,
                ),
                DocumentMetadataRecord(
                    document_id=5,
                    file_name="FCA_SUP_17_Transaction_Reporting.pdf",
                    storage_path="reg-iris-docs/FCA_SUP_17_Transaction_Reporting.pdf",
                    regulator="FCA",
                    jurisdiction="UK",
                    effective_date=datetime.date(2024, 3, 31),
                    category="MARKET_ABUSE",
                    version="v1.1",
                    parent_doc_id=None,
                ),
            ]
            db.add_all(records)
            db.commit()

            # Seed initial What's New alert for EMIR v2.0
            alert = RegulatoryAlertRecord(
                document_id=2,
                regulator="EMIR",
                document_title="EMIR_Technical_Standards_v2.0.pdf",
                version="v2.0",
                effective_date=datetime.date(2026, 1, 15),
                diff_summary="EMIR Refit revision: Mandates Unique Product Identifier (UPI), dual-sided Unique Trade Identifier (UTI) matching, and GLEIF LEI pre-validation.",
                impact_level="HIGH",
                is_read=False,
            )
            db.add(alert)
            db.commit()
            logger.info("Seeded 5 document metadata records and baseline alerts.")

        # 2. Index clauses into Elasticsearch
        elasticsearch_client.index_clauses(INITIAL_CLAUSES)

        # 3. Embed and store clauses into ChromaDB
        chroma_ids = [c["chunkId"] for c in INITIAL_CLAUSES]
        chroma_texts = [c["text"] for c in INITIAL_CLAUSES]
        chroma_metas = [
            {
                "chunk_id": c["chunkId"],
                "document_id": str(c["documentId"]),
                "file_name": c["fileName"],
                "regulator": c["regulator"],
                "jurisdiction": c["jurisdiction"],
                "category": c["category"],
                "page_number": str(c["pageNumber"]),
                "parent_section_id": c["parentSectionId"],
            }
            for c in INITIAL_CLAUSES
        ]

        try:
            embeddings = embedding_service.embed_batch(chroma_texts)
            chroma_client.add_documents(
                ids=chroma_ids,
                embeddings=embeddings,
                documents=chroma_texts,
                metadatas=chroma_metas,
            )
            logger.info("Seeded %d clauses into ChromaDB vector store.", len(INITIAL_CLAUSES))
        except Exception as ce:
            logger.warning("ChromaDB seeding deferred: %s", ce)

    except Exception as exc:
        logger.error("Error during initial seeding: %s", exc)
    finally:
        db.close()
