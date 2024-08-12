import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel


class Contact(BaseModel):
    name: str
    job: str


app = FastAPI()


@app.get('/api/people/{area}')
def get_people(area: str) -> list[Contact]:
    # Step 1 - Create file path
    full_filename = Path(__file__).parents[0] / '..' / 'data_files' / f"{area}.txt"

    # Step 2 -  read file into a list of strings
    with open(full_filename) as infile:
        buf = infile.read()
        lines = [l for l in buf.split("\n") if l.strip()]

    # Step 3 - Parse each JSON into a dictionary
    json_recs = [json.loads(line) for line in lines]

    # Step 4 - Convert each json record into a Pydantic Model
    contacts = [Contact(**rec) for rec in json_recs]

    return contacts


if __name__ == '__main__':
    from uvicorn import run
    run(app)