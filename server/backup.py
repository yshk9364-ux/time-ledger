#!/usr/bin/env python3
"""Take a consistent SQLite snapshot; never expose backups through nginx."""
import sqlite3,datetime,os
from pathlib import Path
source=Path(os.environ.get('LEDGER_DB','/var/lib/time-ledger/ledger.sqlite3'))
folder=Path(os.environ.get('BACKUP_DIR','/var/backups/time-ledger'));folder.mkdir(parents=True,exist_ok=True);os.chmod(folder,0o700)
name=folder/('ledger-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')+'.sqlite3')
with sqlite3.connect(source) as src,sqlite3.connect(name) as dst:src.backup(dst)
os.chmod(name,0o600)
for old in sorted(folder.glob('ledger-*.sqlite3'))[:-14]:old.unlink()
print('Database backup completed')
