# BackupGD

Back up file or directory as gzipped tar file on GoogleDrive.

## Requirements

- Python3.9 or later

Optionals

- client_secret.json (OAuth Client ID from Google Cloud Platform)

See also https://developers.google.com/workspace/guides/create-credentials


## Installation
```
pip install git+https://github.com/hinihat/backupGD
```

## Example
```python
import backupGD

tarfile = backupGD.create_backup('./data') # Create gzipped tar file
with backupGD.drive() as drive:
    folder_id = drive.create_folder('backupGD') # Create folder on GoogleDrive
    drive.upload_backup(tarfile, folder_id=folder_id) # Upload tar file
```

## CLI
```shell
$ backupGD --help
usage: backupGD [optional arguments]

optional arguments:
  -h, --help            show this help message and exit
  --log-level {critical,error,warning,info,debug}
                        logging level [default: info]
  --version             show version
  --name TEXT           folder name on GoogleDrive [default: backupGD]
  --path PATH           path to file or directory to back up [default:
                        /workspaces/backupGD/data]
  --every INTEGER       interval [default: 1]
  --day {days,sunday,monday,tuesday,wednesday,thursday,friday,saturday,weeks}
                        days to keep in drive [default: days]
  --at TEXT             time to run [default: 00:00]
  --keep INTEGER        max number of backup files on GoogleDrive [default: 16]
  --client-secret PATH  path to client_secret.json [default:
                        /workspaces/backupGD/client_secret.json]
  --token PATH          path to OAuth2.0 token [default: /workspaces/backupGD/token.json]

$ backupBD --name backup --path ./data --day sunday --at 12:00
```

## Docker
```shell
$ docker run --rm hinihat/backupgd --help
# The same content as CLI help
```

```yaml
version: "3.4"

services:
  backupGD:
    image: hinihat/backupGD
    restart: always
    volumes:
      - type: bind
        source: ./data
        target: /backupGD/data
        read_only: true
      - type: bind
        source: token.json
        target: /backupGD/token.json
    command: --every 3

  # Other services here
```
In order to get `token.json`, run the following script.
```python
import backupGD
credentials = backupGD.get_credentials()
with open('token.json', 'w') as f:
    f.write(credentials.to_json())
```

## License
MIT License
