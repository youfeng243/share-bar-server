# version_file

## Install

Create virtualenv
```
virtualenv -p python3 venv
```

Activate it
```
cd venv
. bin/activate
```

Git clone
```
git clone ....
```

Install requirements
```
cd version_file
pip install -r requirements.txt
```

Run app
```
python file_server.py
```

## Usage

`GET /`: HTML upload interface

`POST /data`: Upload data

form-data: {key: data, value: FILE}

`POST /download`: Download using JSON

Content-Type: application/json
```
{
  "game": "LOL",
  "version": "2017-10-25"
}
```

`DELETE /data/<game>` Delete game. 

`game`: game to be deleted

`GET /data/<game>/<version>` Download using params. 

`game`: game to be downloaded, `version`: version