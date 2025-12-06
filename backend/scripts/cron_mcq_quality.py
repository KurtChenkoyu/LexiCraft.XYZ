#!/usr/bin/env python3
"""
Scheduled Task: MCQ Quality Recalculation

Run this periodically (e.g., hourly or daily) to:
1. Recalculate quality metrics for MCQs with new attempts
2. Flag low-quality MCQs for review
3. Update difficulty and discrimination indices

Usage:
    # Run manually
    python scripts/cron_mcq_quality.py
    
    # Add to crontab (run every hour)
    0 * * * * cd /path/to/backend && source venv/bin/activate && python scripts/cron_mcq_quality.py >> /var/log/mcq_quality.log 2>&1
    
    # Or run daily at 2 AM
    0 2 * * * cd /path/to/backend && source venv/bin/activate && python scripts/cron_mcq_quality.py >> /var/log/mcq_quality.log 2>&1
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.postgres_connection import PostgresConnection
from src.mcq_adaptive import MCQAdaptiveService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_quality_recalculation():
    """Main function to recalculate MCQ quality metrics."""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info(f"MCQ Quality Recalculation Started: {start_time}")
    logger.info("="*60)
    
    try:
        # Connect to database
        pg_conn = PostgresConnection()
        if not pg_conn.verify_connectivity():
            logger.error("Failed to connect to PostgreSQL")
            return False
        
        db = pg_conn.get_session()
        service = MCQAdaptiveService(db)
        
        # Get current quality report
        report_before = service.get_quality_report()
        logger.info(f"Before recalculation:")
        logger.info(f"  Total MCQs: {report_before['total_mcqs']}")
        logger.info(f"  Needs Review: {report_before['needs_review']}")
        logger.info(f"  Total Attempts: {report_before['total_attempts']}")
        
        # Recalculate quality metrics
        logger.info("\nRecalculating quality metrics...")
        count = service.trigger_quality_recalculation()
        logger.info(f"  Recalculated: {count} MCQs")
        
        # Get updated report
        report_after = service.get_quality_report()
        logger.info(f"\nAfter recalculation:")
        logger.info(f"  Quality Distribution:")
        for level, count in report_after['quality_distribution'].items():
            logger.info(f"    {level}: {count}")
        
        if report_after['avg_quality_score']:
            logger.info(f"  Avg Quality Score: {report_after['avg_quality_score']:.3f}")
        
        # Check for MCQs needing attention
        issues = service.get_mcqs_needing_attention(limit=10)
        if issues:
            logger.warning(f"\n⚠️ {len(issues)} MCQs need attention:")
            for item in issues[:5]:
                logger.warning(f"  - {item['word']} ({item['mcq_type']}): {item['reason']}")
            if len(issues) > 5:
                logger.warning(f"  ... and {len(issues) - 5} more")
        else:
            logger.info("\n✅ No MCQs need attention")
        
        # Cleanup
        db.close()
        pg_conn.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"\n✅ Quality recalculation completed in {duration:.2f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"Quality recalculation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Entry point."""
    success = run_quality_recalculation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

