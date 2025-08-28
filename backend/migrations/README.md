# Database Migrations

This directory contains database migration scripts for the GUARDIAN system.

## Document Type Categorization Migration

The `add_document_types` migration adds document categorization support to distinguish between:

- **Ground Truth Documents**: European Pharmacopoeia standards, regulatory guidelines
- **Protocol Documents**: User-uploaded protocols to be analyzed  
- **Reference Documents**: Additional reference materials
- **Analysis Results**: Generated analysis reports

### Migration Files

1. **`add_document_types.sql`** - Raw SQL migration script
   - Can be run directly against PostgreSQL database
   - Includes rollback instructions (commented out)

2. **`add_document_types_alembic.py`** - Alembic migration script
   - For use when Alembic is initialized in the project
   - Includes both upgrade() and downgrade() functions

### Running Migrations

#### Option 1: Direct SQL Execution
```bash
# Connect to your PostgreSQL database and run:
psql -U your_user -d guardian -f backend/migrations/add_document_types.sql
```

#### Option 2: Using Alembic (Recommended for Production)
```bash
# Initialize Alembic (first time only)
cd backend
alembic init alembic

# Copy the migration file to alembic/versions/
cp migrations/add_document_types_alembic.py alembic/versions/001_add_document_types.py

# Run the migration
alembic upgrade head
```

### Schema Changes

The migration adds the following to the `documents` table:

```sql
-- New columns
document_type document_type DEFAULT 'protocol'
document_category document_category DEFAULT 'other'

-- New indexes  
idx_documents_type
idx_documents_category
idx_documents_type_category
```

### Document Types

- `ground_truth`: European Pharmacopoeia standards, regulatory documents
- `protocol`: User protocols to be analyzed against standards
- `reference`: Additional reference materials and documentation  
- `analysis_result`: Generated compliance analysis reports

### Document Categories

- `european_pharmacopoeia`: European Pharmacopoeia monographs and chapters
- `usp_standard`: United States Pharmacopeia standards
- `ich_guideline`: ICH (International Council for Harmonisation) guidelines
- `fda_guidance`: FDA guidance documents
- `ema_guideline`: EMA (European Medicines Agency) guidelines
- `analytical_method`: Analytical testing procedures
- `quality_control`: Quality control specifications
- `stability_testing`: Stability testing protocols
- `impurity_profiling`: Impurity identification and profiling
- `dissolution_testing`: Dissolution testing methods
- `microbiological`: Microbiological testing procedures
- `cleaning_validation`: Equipment cleaning validation
- `process_validation`: Manufacturing process validation
- `regulatory_submission`: Regulatory submission documents
- `other`: Other document types

### Backward Compatibility

- Existing documents will be assigned default values (`protocol` type, `other` category)
- The migration is non-destructive - no existing data is lost
- Applications can continue to work without immediate code changes
- Document type fields are optional in API requests with sensible defaults

### Testing the Migration

After running the migration, verify the changes:

```sql
-- Check that columns were added
\d documents

-- Check enum types were created
\dT+ document_type
\dT+ document_category

-- Check indexes were created
\di idx_documents_*

-- Check default values on existing data
SELECT document_type, document_category, COUNT(*) 
FROM documents 
GROUP BY document_type, document_category;
```

### Rollback Instructions

If you need to rollback the migration:

#### SQL Rollback
```sql
-- Remove indexes
DROP INDEX IF EXISTS idx_documents_type_category;
DROP INDEX IF EXISTS idx_documents_category;
DROP INDEX IF EXISTS idx_documents_type;

-- Remove columns
ALTER TABLE documents DROP COLUMN IF EXISTS document_category;
ALTER TABLE documents DROP COLUMN IF EXISTS document_type;

-- Remove enums (only if not used elsewhere)
DROP TYPE IF EXISTS document_category;
DROP TYPE IF EXISTS document_type;
```

#### Alembic Rollback
```bash
alembic downgrade -1
```

## Future Migrations

When adding new migrations:

1. Create both SQL and Alembic versions for flexibility
2. Include comprehensive rollback instructions  
3. Test on a copy of production data first
4. Document schema changes and their purpose
5. Update this README with new migration information