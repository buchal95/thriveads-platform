"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-01-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create clients table
    op.create_table('clients',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('meta_ad_account_id', sa.String(), nullable=False),
        sa.Column('meta_access_token', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=True, default='cs'),
        sa.Column('country', sa.String(), nullable=True, default='CZ'),
        sa.Column('currency', sa.String(), nullable=True, default='CZK'),
        sa.Column('timezone', sa.String(), nullable=True, default='Europe/Prague'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('meta_ad_account_id')
    )
    op.create_index(op.f('ix_clients_id'), 'clients', ['id'], unique=False)

    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('objective', sa.String(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('daily_budget', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('lifetime_budget', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ads table
    op.create_table('ads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=True),
        sa.Column('adset_id', sa.String(), nullable=True),
        sa.Column('creative_id', sa.String(), nullable=True),
        sa.Column('preview_url', sa.Text(), nullable=True),
        sa.Column('facebook_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ad_metrics table
    op.create_table('ad_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ad_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=True, default=0),
        sa.Column('clicks', sa.Integer(), nullable=True, default=0),
        sa.Column('spend', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('conversions', sa.Integer(), nullable=True, default=0),
        sa.Column('conversion_value', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('ctr', sa.Numeric(precision=5, scale=4), nullable=True, default=0),
        sa.Column('cpc', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('cpm', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('roas', sa.Numeric(precision=10, scale=4), nullable=True, default=0),
        sa.Column('frequency', sa.Numeric(precision=5, scale=2), nullable=True, default=0),
        sa.Column('attribution', sa.String(), nullable=True, default='default'),
        sa.Column('currency', sa.String(), nullable=True, default='CZK'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['ad_id'], ['ads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create campaign_metrics table
    op.create_table('campaign_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=True, default=0),
        sa.Column('clicks', sa.Integer(), nullable=True, default=0),
        sa.Column('spend', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('conversions', sa.Integer(), nullable=True, default=0),
        sa.Column('conversion_value', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('ctr', sa.Numeric(precision=5, scale=4), nullable=True, default=0),
        sa.Column('cpc', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('cpm', sa.Numeric(precision=10, scale=2), nullable=True, default=0),
        sa.Column('roas', sa.Numeric(precision=10, scale=4), nullable=True, default=0),
        sa.Column('frequency', sa.Numeric(precision=5, scale=2), nullable=True, default=0),
        sa.Column('attribution', sa.String(), nullable=True, default='default'),
        sa.Column('currency', sa.String(), nullable=True, default='CZK'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create data_sync_log table
    op.create_table('data_sync_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('sync_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attribution', sa.String(), nullable=True, default='default'),
        sa.Column('records_processed', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create performance indexes
    op.create_index('idx_ad_metrics_ad_date', 'ad_metrics', ['ad_id', 'date'])
    op.create_index('idx_ad_metrics_date_roas', 'ad_metrics', ['date', sa.text('roas DESC')])
    op.create_index('idx_campaign_metrics_campaign_date', 'campaign_metrics', ['campaign_id', 'date'])
    op.create_index('idx_data_sync_log_client_date', 'data_sync_log', ['client_id', 'sync_date'])
    op.create_index('idx_data_sync_log_status', 'data_sync_log', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_data_sync_log_status', table_name='data_sync_log')
    op.drop_index('idx_data_sync_log_client_date', table_name='data_sync_log')
    op.drop_index('idx_campaign_metrics_campaign_date', table_name='campaign_metrics')
    op.drop_index('idx_ad_metrics_date_roas', table_name='ad_metrics')
    op.drop_index('idx_ad_metrics_ad_date', table_name='ad_metrics')
    
    # Drop tables
    op.drop_table('data_sync_log')
    op.drop_table('campaign_metrics')
    op.drop_table('ad_metrics')
    op.drop_table('ads')
    op.drop_table('campaigns')
    op.drop_index(op.f('ix_clients_id'), table_name='clients')
    op.drop_table('clients')
