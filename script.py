import os
import json
import shutil
import boto3
import paramiko
import subprocess
import schedule
import time
import tqdm
import argparse
from datetime import datetime, timedelta
from mysql.connector import connect
import psycopg2
from dotenv import load_dotenv
from prettytable import PrettyTable
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_timestamp():
    return datetime.now().strftime("%d_%b_%Y_%H-%M-%S")

# Load environment variables
load_dotenv()

def save_backup_record(backup_file, storage_type):
    record_file = "backup_records.json"
    records = []
    if os.path.exists(record_file):
        with open(record_file, "r") as f:
            records = json.load(f)
    records.append({"timestamp": get_timestamp(), "file": backup_file, "storage": storage_type})
    with open(record_file, "w") as f:
        json.dump(records, f, indent=4)

from datetime import datetime, timedelta
import os
import json
from prettytable import PrettyTable

def time_ago(timestamp_str):
    """Converts timestamp into a human-readable format (e.g., '5 minutes ago')."""
    timestamp = datetime.strptime(timestamp_str, "%d_%b_%Y_%H-%M-%S")
    now = datetime.now()
    diff = now - timestamp

    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())} seconds ago"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} minutes ago"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} hours ago"
    elif diff.total_seconds() < 30 * 86400:
        return f"{int(diff.total_seconds() // 86400)} days ago"
    elif diff.total_seconds() < 365 * 86400:
        return f"{int(diff.total_seconds() // (30 * 86400))} months ago"
    else:
        return f"{int(diff.total_seconds() // (365 * 86400))} years ago"

def list_backups():
    """Displays available backups with total count and size per format along with overall total size."""
    record_file = "backup_records.json"
    if not os.path.exists(record_file):
        print("No backups found.")
        return [], {}

    with open(record_file, "r") as f:
        records = json.load(f)

    if not records:
        print("No backup records found.")
        return [], {}

    table = PrettyTable()
    table.field_names = ["No.", "Database Name", "Timestamp", "Time Ago", "Storage Type", "File Size", "Compression Format"]

    valid_backups = []
    format_counts = {}  # To track number of backups per format
    total_size_by_format = {}  # Track total size of backups per format
    total_size = 0  # Overall total size

    for i, record in enumerate(records):
        if not isinstance(record, dict) or "file" not in record:
            continue

        file_path = record["file"]
        if not os.path.exists(file_path):
            continue

        file_size_bytes = os.path.getsize(file_path)
        total_size += file_size_bytes
        valid_backups.append(record)

        file_size = f"{file_size_bytes / 1024:.2f} KB"
        compression_format = file_path.split('.')[-1] if '.' in file_path else 'None'

        # Count backups per format
        format_counts[compression_format] = format_counts.get(compression_format, 0) + 1
        total_size_by_format[compression_format] = total_size_by_format.get(compression_format, 0) + file_size_bytes

        # Convert timestamp to human-readable format
        human_readable_time = time_ago(record["timestamp"])

        table.add_row([i + 1, os.path.basename(file_path).split('_backup_')[0], record['timestamp'], human_readable_time, record['storage'], file_size, compression_format])

    print(table)

    # Display total backup count and size per format
    print("\nSummary of Backups by Format:")
    summary_table = PrettyTable()
    summary_table.field_names = ["Format", "Total Backups", "Total Size (MB)"]

    for fmt, count in format_counts.items():
        total_size_mb = total_size_by_format[fmt] / (1024 * 1024)  # Convert bytes to MB
        summary_table.add_row([fmt, count, f"{total_size_mb:.2f} MB"])

    print(summary_table)

    # Display overall total size
    overall_total_size_mb = total_size / (1024 * 1024)
    print(f"\n💾 **Overall Total Backup Size:** {overall_total_size_mb:.2f} MB")

    return valid_backups, {
        "total_size": total_size,
    }

def send_backup_report():
    """Sends an email report about backup statistics."""
    backups, backup_stats = list_backups()  # Fix: Unpack list and stats separately

    if not backups:
        print("No backups found, skipping email report.")
        return

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password, recipient_email]):
        print("❌ Missing email configuration in .env file.")
        return

    total_size_mb = backup_stats.get("total_size", 0) / 1_000_000  # Fix: Use .get() to avoid KeyError
    last_backup_mb = backup_stats.get("last_backup_size", 0) / 1_000_000

    subject = "Backup Report - Database Backup Activity"
    body = f"""
    Hello,

    Here is your latest backup report:

    - 📅 Backups taken this **week**: {backup_stats.get("weekly_count", 0)}
    - 📅 Backups taken this **month**: {backup_stats.get("monthly_count", 0)}
    - 💾 **Total backup size** till date: {total_size_mb:.2f} MB
    - 📁 **Last backup size**: {last_backup_mb:.2f} MB

    Regards,
    (BRUtility) Backup Restore Utility
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        print("📧 Sending email...")
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def store_s3_credentials():
    """Stores AWS S3 credentials securely in an environment file."""
    aws_access_key = input("Enter AWS Access Key: ")
    aws_secret_key = input("Enter AWS Secret Key: ")
    with open(".env", "a") as f:
        f.write(f"AWS_ACCESS_KEY={aws_access_key}\n")
        f.write(f"AWS_SECRET_KEY={aws_secret_key}\n")
    print("AWS credentials stored securely.")

def store_ftp_credentials():
    """Stores FTP credentials securely in an environment file."""
    ftp_host = input("Enter FTP Host: ")
    ftp_user = input("Enter FTP Username: ")
    ftp_password = input("Enter FTP Password: ")
    with open(".env", "a") as f:
        f.write(f"FTP_HOST={ftp_host}\n")
        f.write(f"FTP_USER={ftp_user}\n")
        f.write(f"FTP_PASSWORD={ftp_password}\n")
    print("FTP credentials stored securely.")

def show_progress(message, duration=5):
    print(message)
    for _ in tqdm.tqdm(range(duration), desc=message):
        time.sleep(1)

def backup_mysql(db_name, user, password, host, backup_dir, compression_format=None):
    """Backs up a MySQL database without prompting for a password."""
    timestamp = get_timestamp()
    backup_file = f"{backup_dir}/{db_name}_backup_{timestamp}.sql"
    show_progress("Backing up MySQL database...")
    
    command = ["mysqldump", "-h", host, "-u", user, f"--password={password}", db_name]
    with open(backup_file, "w") as f:
        subprocess.run(command, stdout=f, check=True)
    
    if compression_format:
        compressed_file = f"{backup_file}.{compression_format}"
        shutil.make_archive(backup_file, compression_format, root_dir=backup_dir, base_dir=os.path.basename(backup_file))
        os.remove(backup_file)
        backup_file = compressed_file
    
    return backup_file

def restore_mysql(db_name, user, password, host, backup_file):
    """Restores a MySQL database without prompting for a password."""
    show_progress("Restoring MySQL database...")
    command = ["mysql", "-h", host, "-u", user, f"--password={password}", db_name]
    with open(backup_file, "r") as f:
        subprocess.run(command, stdin=f, check=True)

def main():
    parser = argparse.ArgumentParser(description="Database Backup and Restore Utility")
    parser.add_argument("--action", choices=["backup", "restore", "list", "email"], required=True, help="Specify action (backup, restore, list, email)")
    parser.add_argument("--compression", choices=["zip", "tar", "gz"], help="Optional compression format (zip, tar, gz)")
    parser.add_argument("--db_type", choices=["mysql", "pgsql"], required=False, help="Database type")
    parser.add_argument("--db_name", required=False, help="Database name")
    parser.add_argument("--user", required=False, help="Database user")
    parser.add_argument("--password", required=False, help="Database password")
    parser.add_argument("--host", required=False, help="Database host")
    parser.add_argument("--storage_type", choices=["local", "s3", "ftp"], help="Storage location for backup")
    args = parser.parse_args()
    
    backup_dir = "./backups"
    os.makedirs(backup_dir, exist_ok=True)

    if args.storage_type == "s3" and (not os.getenv("AWS_ACCESS_KEY") or not os.getenv("AWS_SECRET_KEY")):
        store_s3_credentials()

    if args.storage_type == "ftp" and (not os.getenv("FTP_HOST") or not os.getenv("FTP_USER") or not os.getenv("FTP_PASSWORD")):
        store_ftp_credentials()

    if args.action == "backup":
        if args.db_type == "mysql":
            backup_file = backup_mysql(args.db_name, args.user, args.password, args.host, backup_dir, args.compression)
        else:
            print("Unsupported database type")
            return
        
        save_backup_record(backup_file, args.storage_type or "local")
        print(f"Backup saved as {backup_file} in {args.storage_type or 'local'}.")
    
    elif args.action == "list":
        print("Listing all available backups:")
        list_backups()
    elif args.action == "email":
        send_backup_report()
    
    elif args.action == "restore":
        backups, _ = list_backups()  # Ensure this returns a list

        if not backups:
            print("No backups available for restoration.")
            return

        try:
            backup_choice = int(input("Select the backup number to restore: ")) - 1
            if backup_choice < 0 or backup_choice >= len(backups):
                raise ValueError("Invalid choice.")
        except ValueError:
            print("❌ Invalid input. Please enter a valid number.")
            return
        
        selected_backup = backups[backup_choice]  # Fix: Ensure this is a dictionary
        if not isinstance(selected_backup, dict):
            print("❌ Error: Selected backup is invalid.")
            return

        backup_file = selected_backup.get("file")  # Safely get file path

        if not backup_file or not os.path.exists(backup_file):
            print(f"❌ Selected backup file not found: {backup_file}")
            return

        print(f"✅ Restoring backup: {backup_file}")

        if args.db_type == "mysql":
            restore_mysql(args.db_name, args.user, args.password, args.host, backup_file)
        else:
            print("❌ Unsupported database type.")
            return

        print("✅ Database restored successfully.")


if __name__ == "__main__":
    main()