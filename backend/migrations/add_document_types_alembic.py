"""Add document type and category fields

Revision ID: add_document_types_001
Revises: 
Create Date: 2025-06-30 12:00:00.000000

This migration adds document categorization support to the GUARDIAN system:
- Adds document_type enum and column
- Adds document_category enum and column  
- Creates indexes for performance
- Sets default values for existing data

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_document_types_001'
down_revision = None
branch_labels = None
depends_on = None

# Define the enum types
document_type_enum = postgresql.ENUM(
    'ground_truth', 'protocol', 'reference', 'analysis_result',
    name='document_type'
)

document_category_enum = postgresql.ENUM(
    'european_pharmacopoeia', 'usp_standard', 'ich_guideline', 'fda_guidance',
    'ema_guideline', 'analytical_method', 'quality_control', 'stability_testing',
    'impurity_profiling', 'dissolution_testing', 'microbiological', 
    'cleaning_validation', 'process_validation', 'regulatory_submission', 'other',
    name='document_category'
)

def upgrade():
    """Add document type and category fields to documents table."""
    
    # Create the enum types
    document_type_enum.create(op.get_bind(), checkfirst=True)
    document_category_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns to documents table
    op.add_column('documents', sa.Column(
        'document_type', 
        document_type_enum, 
        nullable=False, 
        server_default='protocol'
    ))
    
    op.add_column('documents', sa.Column(
        'document_category', 
        document_category_enum, 
        nullable=False, 
        server_default='other'
    ))
    
    # Create indexes for better query performance
    op.create_index('idx_documents_type', 'documents', ['document_type'])
    op.create_index('idx_documents_category', 'documents', ['document_category'])
    op.create_index('idx_documents_type_category', 'documents', ['document_type', 'document_category'])
    
    # Update any existing documents to have default values
    # This should be automatic due to server_default, but included for safety
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE documents 
        SET document_type = 'protocol', document_category = 'other'
        WHERE document_type IS NULL OR document_category IS NULL
    """))


def downgrade():
    """Remove document type and category fields from documents table."""
    
    # Remove indexes
    op.drop_index('idx_documents_type_category')
    op.drop_index('idx_documents_category') 
    op.drop_index('idx_documents_type')
    
    # Remove columns
    op.drop_column('documents', 'document_category')
    op.drop_column('documents', 'document_type')
    
    # Drop enum types
    document_category_enum.drop(op.get_bind(), checkfirst=True)
    document_type_enum.drop(op.get_bind(), checkfirst=True)