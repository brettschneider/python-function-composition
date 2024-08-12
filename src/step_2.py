import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel


class Contact(BaseModel):
    name: str
    job: str


app = FastAPI()


def create_filepath(area: str) -> Path:
    """Step 1 - Create file path"""
    return Path(__file__).parents[0] / '..' / 'data_files' / f"{area}.txt"


def read_lines(file_path: Path) -> list[str]:
    """Step 2 -  read file into a list of strings"""
    with open(file_path) as infile:
        buf = infile.read()
        return [l for l in buf.split("\n") if l.strip()]


def parse_dicts(lines: list[str]) -> list[dict]:
    """Step 3 - Parse each JSON into a dictionary"""
    return [json.loads(line) for line in lines]


def convert_to_contacts(dicts: list[dict]) -> list[Contact]:
    """Step 4 - Convert each json record into a Pydantic Model"""
    return [Contact(**rec) for rec in dicts]


@app.get('/api/people/{area}')
def get_people(area: str) -> list[Contact]:
    return convert_to_contacts(parse_dicts(read_lines(create_filepath(area))))


if __name__ == '__main__':
    from uvicorn import run

    run(app)
