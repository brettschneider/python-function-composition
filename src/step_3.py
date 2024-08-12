import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from functools import update_wrapper


class composable:
    """Decorator that allows chaining of simple functions"""

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __call__(self, *args):
        return self.func(*args)

    def __ror__(self, other):
        args = other
        if isinstance(args, (list, tuple)):
            args = [i() if callable(i) else i for i in args]
        if isinstance(args, dict):
            args = {k: v() if callable(v) else v for k, v in args.items()}
        return self.func(args)

    def __or__(self, other):
        if callable(other):
            return composable(lambda value: other(self.func(value)))
        return composable(lambda x: self.func(other))


class Contact(BaseModel):
    name: str
    job: str


app = FastAPI()


@composable
def create_filepath(area: str) -> Path:
    """Step 1 - Create file path"""
    return Path(__file__).parents[0] / '..' / 'data_files' / f"{area}.txt"


@composable
def read_lines(file_path: Path) -> list[str]:
    """Step 2 -  read file into a list of strings"""
    with open(file_path) as infile:
        buf = infile.read()
        return [l for l in buf.split("\n") if l.strip()]


@composable
def parse_dicts(lines: list[str]) -> list[dict]:
    """Step 3 - Parse each JSON into a dictionary"""
    return [json.loads(line) for line in lines]


@composable
def convert_to_contacts(dicts: list[dict]) -> list[Contact]:
    """Step 4 - Convert each json record into a Pydantic Model"""
    return [Contact(**rec) for rec in dicts]


@app.get('/api/people/{area}')
def get_people(area: str) -> list[Contact]:
    return area | create_filepath | read_lines | parse_dicts | convert_to_contacts


if __name__ == '__main__':
    from uvicorn import run

    run(app)
