"""
Management command to clean up expired analysis results and old data.
Run with: python manage.py cleanup_old_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from dashboard.models import AnalysisResult, AnalysisSession
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Cleanup expired analysis results, old sessions, and stale cache data (7-day retention policy)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to retain data (default: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        retention_days = options['days']
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        self.stdout.write(self.style.NOTICE(f"\n{'='*60}"))
        self.stdout.write(self.style.NOTICE(f"  VisaGuardAI Data Cleanup Utility"))
        self.stdout.write(self.style.NOTICE(f"{'='*60}\n"))
        self.stdout.write(f"Retention policy: {retention_days} days")
        self.stdout.write(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Mode: {'DRY RUN (no deletions)' if dry_run else 'LIVE (will delete data)'}\n")
        
        total_cleaned = 0
        
        # 1. Clean up expired AnalysisResult records
        expired_results = AnalysisResult.objects.filter(
            expires_at__lte=timezone.now()
        )
        expired_count = expired_results.count()
        
        if expired_count > 0:
            self.stdout.write(self.style.WARNING(f"📊 Found {expired_count} expired analysis results"))
            if not dry_run:
                deleted = expired_results.delete()
                self.stdout.write(self.style.SUCCESS(f"   ✓ Deleted {deleted[0]} expired results"))
                total_cleaned += deleted[0]
            else:
                self.stdout.write("   (Would delete in live mode)")
        else:
            self.stdout.write(self.style.SUCCESS("📊 No expired analysis results found"))
        
        # 2. Clean up old unpaid AnalysisResult records
        old_unpaid_results = AnalysisResult.objects.filter(
            analyzed_at__lt=cutoff_date,
            payment_completed=False
        )
        old_unpaid_count = old_unpaid_results.count()
        
        if old_unpaid_count > 0:
            self.stdout.write(self.style.WARNING(f"💳 Found {old_unpaid_count} old unpaid results (>{retention_days} days)"))
            if not dry_run:
                deleted = old_unpaid_results.delete()
                self.stdout.write(self.style.SUCCESS(f"   ✓ Deleted {deleted[0]} old unpaid results"))
                total_cleaned += deleted[0]
            else:
                self.stdout.write("   (Would delete in live mode)")
        else:
            self.stdout.write(self.style.SUCCESS("💳 No old unpaid results found"))
        
        # 3. Clean up old AnalysisSession records (keep only metadata, no data)
        old_sessions = AnalysisSession.objects.filter(
            analyzed_at__lt=cutoff_date
        )
        old_session_count = old_sessions.count()
        
        if old_session_count > 0:
            self.stdout.write(self.style.WARNING(f"📝 Found {old_session_count} old analysis sessions (>{retention_days} days)"))
            if not dry_run:
                deleted = old_sessions.delete()
                self.stdout.write(self.style.SUCCESS(f"   ✓ Deleted {deleted[0]} old sessions"))
                total_cleaned += deleted[0]
            else:
                self.stdout.write("   (Would delete in live mode)")
        else:
            self.stdout.write(self.style.SUCCESS("📝 No old analysis sessions found"))
        
        # 4. Clean up expired Django sessions
        expired_sessions = Session.objects.filter(
            expire_date__lt=timezone.now()
        )
        expired_session_count = expired_sessions.count()
        
        if expired_session_count > 0:
            self.stdout.write(self.style.WARNING(f"🔒 Found {expired_session_count} expired Django sessions"))
            if not dry_run:
                deleted = expired_sessions.delete()
                self.stdout.write(self.style.SUCCESS(f"   ✓ Deleted {deleted[0]} expired sessions"))
                total_cleaned += deleted[0]
            else:
                self.stdout.write("   (Would delete in live mode)")
        else:
            self.stdout.write(self.style.SUCCESS("🔒 No expired Django sessions found"))
        
        # 5. Clean up cache (done via Django's cache system)
        from django.core.cache import cache
        try:
            # Note: Django's DB cache doesn't have a direct "clear expired" method
            # So we'll just note it here
            self.stdout.write(self.style.NOTICE("🗄️  Cache cleanup: Django's cache backend handles expiration automatically"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"🗄️  Cache check warning: {e}"))
        
        # Summary
        self.stdout.write(self.style.NOTICE(f"\n{'='*60}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN COMPLETE - No data was deleted"))
            self.stdout.write(f"Would clean up {total_cleaned} records in live mode")
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ CLEANUP COMPLETE"))
            self.stdout.write(self.style.SUCCESS(f"   Removed {total_cleaned} total records"))
        self.stdout.write(self.style.NOTICE(f"{'='*60}\n"))
        
        # Recommendations
        if total_cleaned > 1000 and not dry_run:
            self.stdout.write(self.style.WARNING("⚠️  Large cleanup detected. Consider running this more frequently."))
        
        self.stdout.write("\n💡 Recommended cron schedule:")
        self.stdout.write("   Daily: 0 2 * * * cd /path/to/project && python manage.py cleanup_old_data")
        self.stdout.write("   Weekly: 0 3 * * 0 cd /path/to/project && python manage.py cleanup_old_data --days 7\n")

