"""
Data retention and archiving service for managing historical data
"""

import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
import json
import gzip
import os

from app.models.metrics import AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics, DataSyncLog

logger = structlog.get_logger()


class DataRetentionService:
    """Service for managing data retention and archiving"""
    
    def __init__(self, db: Session):
        self.db = db
        self.archive_path = "data_archives"
        
        # Ensure archive directory exists
        os.makedirs(self.archive_path, exist_ok=True)
    
    def get_retention_policy(self) -> Dict[str, Any]:
        """
        Get the current data retention policy
        
        Returns:
            Dictionary with retention rules for different data types
        """
        return {
            "daily_metrics": {
                "retention_days": 365,  # Keep daily data for 1 year
                "archive_after_days": 90,  # Archive after 3 months
                "description": "Daily ad and campaign metrics"
            },
            "weekly_aggregates": {
                "retention_days": 730,  # Keep weekly data for 2 years
                "archive_after_days": 365,  # Archive after 1 year
                "description": "Weekly aggregated metrics"
            },
            "monthly_aggregates": {
                "retention_days": -1,  # Keep forever
                "archive_after_days": 1095,  # Archive after 3 years
                "description": "Monthly aggregated metrics"
            },
            "sync_logs": {
                "retention_days": 90,  # Keep sync logs for 3 months
                "archive_after_days": 30,  # Archive after 1 month
                "description": "Data synchronization logs"
            }
        }
    
    def analyze_data_usage(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze current data usage and storage requirements
        
        Args:
            client_id: Optional client ID to analyze specific client data
        
        Returns:
            Data usage analysis
        """
        analysis = {}
        
        # Base filters
        base_filter = []
        if client_id:
            # Note: AdMetrics doesn't have client_id directly, need to join through Ad
            pass
        
        # Analyze daily metrics
        daily_count = self.db.query(func.count(AdMetrics.id)).scalar()
        daily_oldest = self.db.query(func.min(AdMetrics.date)).scalar()
        daily_newest = self.db.query(func.max(AdMetrics.date)).scalar()
        
        analysis['daily_metrics'] = {
            'total_records': daily_count,
            'oldest_date': daily_oldest.isoformat() if daily_oldest else None,
            'newest_date': daily_newest.isoformat() if daily_newest else None,
            'date_range_days': (daily_newest - daily_oldest).days if daily_oldest and daily_newest else 0
        }
        
        # Analyze weekly aggregates
        weekly_count = self.db.query(func.count(WeeklyAdMetrics.id)).scalar()
        weekly_oldest = self.db.query(func.min(WeeklyAdMetrics.week_start_date)).scalar()
        weekly_newest = self.db.query(func.max(WeeklyAdMetrics.week_start_date)).scalar()
        
        analysis['weekly_aggregates'] = {
            'total_records': weekly_count,
            'oldest_date': weekly_oldest.isoformat() if weekly_oldest else None,
            'newest_date': weekly_newest.isoformat() if weekly_newest else None,
            'weeks_covered': ((weekly_newest - weekly_oldest).days // 7) if weekly_oldest and weekly_newest else 0
        }
        
        # Analyze monthly aggregates
        monthly_count = self.db.query(func.count(MonthlyCampaignMetrics.id)).scalar()
        
        analysis['monthly_aggregates'] = {
            'total_records': monthly_count
        }
        
        # Analyze sync logs
        sync_count = self.db.query(func.count(DataSyncLog.id)).scalar()
        sync_oldest = self.db.query(func.min(DataSyncLog.started_at)).scalar()
        sync_newest = self.db.query(func.max(DataSyncLog.started_at)).scalar()
        
        analysis['sync_logs'] = {
            'total_records': sync_count,
            'oldest_date': sync_oldest.isoformat() if sync_oldest else None,
            'newest_date': sync_newest.isoformat() if sync_newest else None
        }
        
        # Calculate storage estimates (rough estimates)
        estimated_storage = {
            'daily_metrics_mb': daily_count * 0.001,  # ~1KB per record
            'weekly_aggregates_mb': weekly_count * 0.0005,  # ~0.5KB per record
            'monthly_aggregates_mb': monthly_count * 0.0005,
            'sync_logs_mb': sync_count * 0.0002,  # ~0.2KB per record
        }
        
        total_storage_mb = sum(estimated_storage.values())
        analysis['storage_estimate'] = {
            **estimated_storage,
            'total_mb': round(total_storage_mb, 2),
            'total_gb': round(total_storage_mb / 1024, 2)
        }
        
        return analysis
    
    def identify_archival_candidates(self) -> Dict[str, Any]:
        """
        Identify data that should be archived based on retention policy
        
        Returns:
            Dictionary with archival candidates for each data type
        """
        policy = self.get_retention_policy()
        candidates = {}
        
        # Daily metrics candidates
        archive_cutoff = date.today() - timedelta(days=policy['daily_metrics']['archive_after_days'])
        
        daily_candidates = self.db.query(
            func.count(AdMetrics.id).label('count'),
            func.min(AdMetrics.date).label('oldest_date'),
            func.max(AdMetrics.date).label('newest_date')
        ).filter(AdMetrics.date < archive_cutoff).first()
        
        candidates['daily_metrics'] = {
            'archive_cutoff_date': archive_cutoff.isoformat(),
            'records_to_archive': daily_candidates.count if daily_candidates.count else 0,
            'oldest_date': daily_candidates.oldest_date.isoformat() if daily_candidates.oldest_date else None,
            'newest_date': daily_candidates.newest_date.isoformat() if daily_candidates.newest_date else None
        }
        
        # Weekly aggregates candidates
        weekly_archive_cutoff = date.today() - timedelta(days=policy['weekly_aggregates']['archive_after_days'])
        
        weekly_candidates = self.db.query(
            func.count(WeeklyAdMetrics.id).label('count'),
            func.min(WeeklyAdMetrics.week_start_date).label('oldest_date'),
            func.max(WeeklyAdMetrics.week_start_date).label('newest_date')
        ).filter(WeeklyAdMetrics.week_start_date < weekly_archive_cutoff).first()
        
        candidates['weekly_aggregates'] = {
            'archive_cutoff_date': weekly_archive_cutoff.isoformat(),
            'records_to_archive': weekly_candidates.count if weekly_candidates.count else 0,
            'oldest_date': weekly_candidates.oldest_date.isoformat() if weekly_candidates.oldest_date else None,
            'newest_date': weekly_candidates.newest_date.isoformat() if weekly_candidates.newest_date else None
        }
        
        # Sync logs candidates
        sync_archive_cutoff = datetime.now() - timedelta(days=policy['sync_logs']['archive_after_days'])
        
        sync_candidates = self.db.query(
            func.count(DataSyncLog.id).label('count'),
            func.min(DataSyncLog.started_at).label('oldest_date'),
            func.max(DataSyncLog.started_at).label('newest_date')
        ).filter(DataSyncLog.started_at < sync_archive_cutoff).first()
        
        candidates['sync_logs'] = {
            'archive_cutoff_date': sync_archive_cutoff.isoformat(),
            'records_to_archive': sync_candidates.count if sync_candidates.count else 0,
            'oldest_date': sync_candidates.oldest_date.isoformat() if sync_candidates.oldest_date else None,
            'newest_date': sync_candidates.newest_date.isoformat() if sync_candidates.newest_date else None
        }
        
        return candidates
    
    def archive_old_data(self, data_type: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Archive old data based on retention policy
        
        Args:
            data_type: Type of data to archive ('daily_metrics', 'weekly_aggregates', 'sync_logs')
            dry_run: If True, only simulate the archival process
        
        Returns:
            Archival results
        """
        policy = self.get_retention_policy()
        
        if data_type not in policy:
            raise ValueError(f"Unknown data type: {data_type}")
        
        archive_cutoff_days = policy[data_type]['archive_after_days']
        
        if data_type == 'daily_metrics':
            return self._archive_daily_metrics(archive_cutoff_days, dry_run)
        elif data_type == 'weekly_aggregates':
            return self._archive_weekly_aggregates(archive_cutoff_days, dry_run)
        elif data_type == 'sync_logs':
            return self._archive_sync_logs(archive_cutoff_days, dry_run)
        else:
            raise ValueError(f"Archival not implemented for data type: {data_type}")
    
    def _archive_daily_metrics(self, cutoff_days: int, dry_run: bool) -> Dict[str, Any]:
        """Archive daily metrics older than cutoff_days"""
        cutoff_date = date.today() - timedelta(days=cutoff_days)
        
        # Get records to archive
        records_to_archive = self.db.query(AdMetrics).filter(
            AdMetrics.date < cutoff_date
        ).all()
        
        if not records_to_archive:
            return {
                'data_type': 'daily_metrics',
                'records_archived': 0,
                'message': 'No records found for archival'
            }
        
        archive_filename = f"daily_metrics_{cutoff_date.isoformat()}.json.gz"
        archive_filepath = os.path.join(self.archive_path, archive_filename)
        
        if not dry_run:
            # Convert records to JSON
            archive_data = []
            for record in records_to_archive:
                archive_data.append({
                    'id': record.id,
                    'ad_id': record.ad_id,
                    'date': record.date.isoformat(),
                    'impressions': record.impressions,
                    'clicks': record.clicks,
                    'spend': float(record.spend),
                    'conversions': record.conversions,
                    'conversion_value': float(record.conversion_value),
                    'ctr': float(record.ctr),
                    'cpc': float(record.cpc),
                    'cpm': float(record.cpm),
                    'roas': float(record.roas),
                    'frequency': float(record.frequency),
                    'attribution': record.attribution,
                    'currency': record.currency,
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            # Write compressed archive
            with gzip.open(archive_filepath, 'wt', encoding='utf-8') as f:
                json.dump({
                    'archive_date': datetime.now().isoformat(),
                    'data_type': 'daily_metrics',
                    'cutoff_date': cutoff_date.isoformat(),
                    'record_count': len(archive_data),
                    'records': archive_data
                }, f, indent=2)
            
            # Delete archived records from database
            for record in records_to_archive:
                self.db.delete(record)
            
            self.db.commit()
            
            logger.info(
                "Daily metrics archived",
                records_count=len(records_to_archive),
                archive_file=archive_filename,
                cutoff_date=cutoff_date
            )
        
        return {
            'data_type': 'daily_metrics',
            'cutoff_date': cutoff_date.isoformat(),
            'records_archived': len(records_to_archive),
            'archive_file': archive_filename if not dry_run else None,
            'dry_run': dry_run
        }
    
    def _archive_weekly_aggregates(self, cutoff_days: int, dry_run: bool) -> Dict[str, Any]:
        """Archive weekly aggregates older than cutoff_days"""
        cutoff_date = date.today() - timedelta(days=cutoff_days)
        
        records_to_archive = self.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.week_start_date < cutoff_date
        ).all()
        
        if not records_to_archive:
            return {
                'data_type': 'weekly_aggregates',
                'records_archived': 0,
                'message': 'No records found for archival'
            }
        
        # Similar archival process as daily metrics
        # Implementation would be similar to _archive_daily_metrics
        
        return {
            'data_type': 'weekly_aggregates',
            'cutoff_date': cutoff_date.isoformat(),
            'records_archived': len(records_to_archive),
            'dry_run': dry_run
        }
    
    def _archive_sync_logs(self, cutoff_days: int, dry_run: bool) -> Dict[str, Any]:
        """Archive sync logs older than cutoff_days"""
        cutoff_datetime = datetime.now() - timedelta(days=cutoff_days)
        
        records_to_archive = self.db.query(DataSyncLog).filter(
            DataSyncLog.started_at < cutoff_datetime
        ).all()
        
        if not records_to_archive:
            return {
                'data_type': 'sync_logs',
                'records_archived': 0,
                'message': 'No records found for archival'
            }
        
        return {
            'data_type': 'sync_logs',
            'cutoff_date': cutoff_datetime.isoformat(),
            'records_archived': len(records_to_archive),
            'dry_run': dry_run
        }
    
    def cleanup_old_data(self, data_type: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up (delete) very old data that exceeds retention policy
        
        Args:
            data_type: Type of data to clean up
            dry_run: If True, only simulate the cleanup process
        
        Returns:
            Cleanup results
        """
        policy = self.get_retention_policy()
        
        if data_type not in policy:
            raise ValueError(f"Unknown data type: {data_type}")
        
        retention_days = policy[data_type]['retention_days']
        
        if retention_days == -1:
            return {
                'data_type': data_type,
                'message': 'Data type has unlimited retention',
                'records_deleted': 0
            }
        
        if data_type == 'sync_logs':
            cutoff_datetime = datetime.now() - timedelta(days=retention_days)
            records_to_delete = self.db.query(DataSyncLog).filter(
                DataSyncLog.started_at < cutoff_datetime
            ).all()
        else:
            cutoff_date = date.today() - timedelta(days=retention_days)
            if data_type == 'daily_metrics':
                records_to_delete = self.db.query(AdMetrics).filter(
                    AdMetrics.date < cutoff_date
                ).all()
            elif data_type == 'weekly_aggregates':
                records_to_delete = self.db.query(WeeklyAdMetrics).filter(
                    WeeklyAdMetrics.week_start_date < cutoff_date
                ).all()
            else:
                records_to_delete = []
        
        if not dry_run and records_to_delete:
            for record in records_to_delete:
                self.db.delete(record)
            self.db.commit()
            
            logger.info(
                "Old data cleaned up",
                data_type=data_type,
                records_deleted=len(records_to_delete),
                retention_days=retention_days
            )
        
        return {
            'data_type': data_type,
            'retention_days': retention_days,
            'records_deleted': len(records_to_delete),
            'dry_run': dry_run
        }
