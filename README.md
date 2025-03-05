
# BRO Tools
BRO (Backup, Restore, and Other Utility tools) is a collection of tools for day-to-day use on your server. This tool helps you to setup automated backup of your database files as well as storage (as of today). However, in future, we will keep adding more tools which can be useful. 

## Why?
There are many tools in the market which satisfy these requirements. However, there are multiple reasons behind developing this tool; such as:

 1. They does not satisfy our requirements 100% (In some case).
 2. Many of them are paid one.
 3. Sometimes it is hard to configure or confusing.
 4. And of course, improve coding skills 😉


## How to use?

### Dependency
* Python (Tested with Python 3.13.2)

### Install required libraries/ packages

```python
pip install -r requirements.txt
```
### Usage
*Using password on command line involve security risk. Use with caution.(See roadmap below)*

```bash
[-h] --action {backup,restore,list,email} [--compression {zip,tar,gz}] [--db_type {mysql,pgsql}]
                 [--db_name DB_NAME] [--user USER] [--password PASSWORD] [--host HOST] [--storage_type {local,s3,ftp}]
```
|Argument| Supported option | Explanation |
|--|--|--|
| --action | backup | Backup database |
|  | restore | Restore database |
|  | list | List available backup on given location |
|  | email | Send email regarding backups |
|  --compression | none| Default .sql format |
| | zip | Compressed into a .zip format file |
| | tar | Tar archive without compression |
| | gz | .tar.gz archive format |
| --db_type | mysql | Backup MySQL database |
| | pgsql | Backup PgSQL database |
| --db_name |  | Database name |
| --user |  | Database user name |
| --password |  | Database password |
| --host |  | Database connection host |
|---storage_type| local | Store backup locally in "backup" directory |
| | s3 | Store backup in configured AWS S3 bucket |
| | ftp | Store backup in configured FTP location |

### Example
1️⃣ Backup MySQL Locally
```
python script.py --action backup --db_type mysql --db_name mydatabase --user root --password mypassword --host localhost --storage_type local
```

2️⃣ List Backups
```
python script.py --action list
```

3️⃣ Restore MySQL
```
python script.py --action restore --db_type mysql --db_name mydatabase --user root --password mypassword --host localhost
```

4️⃣ Send Email Report
```
python script.py --action email
```

🔹 Ensure .env Contains Email Settings
```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=yourpassword
RECIPIENT_EMAIL=recipient@example.com
```


### Roadmap

 1. Store sensitive information such as database credentials and bucket information securely. 
 2. Add support for 
	 * SFTP
	 * GCP Storage
	 * E2E bucket
	 * Dropbox
	 * Google Drive
	 * OneDrive
	 * Amazon S3 Glacier

### Contributing
1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/feature-name`).
3.  Commit your changes (`git commit -m 'Add new feature'`).
4.  Push to the branch (`git push origin feature/feature-name`).
5.  Open a pull request to the main branch.

### Repo Activity
![Alt](https://repobeats.axiom.co/api/embed/30199b300c483cecbc4b15636aa2baf6076ccf82.svg "Repobeats analytics image")

### Security
We take the security of the API extremely seriously. If you think you've found a security issue with the API (whether information disclosure, privilege escalation, or another issue), we'd appreciate responsible disclosure as soon as possible.

To report a security issue, you can email to  `shivampandya24[at]gmail.com`
