#!/bin/bash
# PostgreSQL Database Backup Script for VisaGuardAI

# Configuration
BACKUP_DIR="/Users/davidfinney/Downloads/visaguardai/backups"
DB_NAME="visaguard_db"
DB_USER="davidfinney"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/visaguard_db_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting PostgreSQL backup..."
/opt/homebrew/opt/postgresql@14/bin/pg_dump -U $DB_USER $DB_NAME > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup successful: $BACKUP_FILE"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo "✅ Backup compressed: ${BACKUP_FILE}.gz"
    
    # Keep only last 7 backups
    cd "$BACKUP_DIR"
    ls -t visaguard_db_backup_*.sql.gz | tail -n +8 | xargs -r rm
    echo "✅ Old backups cleaned up (keeping last 7)"
else
    echo "❌ Backup failed"
    exit 1
fi

# Also backup OAuth configuration
echo "Backing up OAuth configuration..."
cd /Users/davidfinney/Downloads/visaguardai
python3 manage.py dumpdata socialaccount account sites --indent 4 > "$BACKUP_DIR/oauth_config_$TIMESTAMP.json"
echo "✅ OAuth configuration backed up"

