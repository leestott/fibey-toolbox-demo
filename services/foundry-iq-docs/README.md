# FoundryIQ Field Operations Knowledge Base

This directory contains internal markdown reference documents for the fiber optics field operations agent. The files in `docs/` are intended to be uploaded to Azure Blob Storage and then indexed by FoundryIQ for retrieval-augmented generation (RAG).

## Contents

- `docs/fiber-splicing-procedures.md`
- `docs/otdr-testing-guide.md`
- `docs/safety-protocols.md`
- `docs/cable-types-reference.md`
- `docs/troubleshooting-guide.md`
- `docs/equipment-specifications.md`
- `docs/installation-standards.md`
- `docs/network-architecture.md`

## Document conventions

- Internal operations tone rather than training-manual tone
- Markdown only; no embedded binaries
- Metadata included at the top of each file (`Last Updated`, `Document Owner`)
- Structured for chunking and indexing with clear section headers, bullets, and tables

## Uploading to Azure Blob Storage

1. Create or identify the target storage account and container used by your FoundryIQ ingestion workflow.
2. Authenticate with Azure CLI:

   ```bash
   az login
   az account set --subscription <subscription-id-or-name>
   ```

3. Upload the markdown files from this directory:

   ```bash
   cd services/foundry-iq-docs
   az storage blob upload-batch \
     --account-name <storage-account-name> \
     --destination <container-name> \
     --source docs \
     --pattern "*.md" \
     --auth-mode login \
     --overwrite
   ```

4. Verify the blobs are present:

   ```bash
   az storage blob list \
     --account-name <storage-account-name> \
     --container-name <container-name> \
     --auth-mode login \
     --output table
   ```

## FoundryIQ indexing notes

- Keep filenames stable so downstream index references do not churn unnecessarily.
- Prefer one topic per file to improve retrieval precision.
- Re-upload changed documents and rerun the FoundryIQ ingestion/indexing job after content updates.
- If your ingestion pipeline uses metadata tags, add them during upload or in the indexing workflow rather than modifying the document body.

## Maintenance

- Update `Last Updated` when technical content changes.
- Keep equipment models, thresholds, and budget references aligned with current field standards.
- Review documents after any major tooling, safety, or network architecture changes.
