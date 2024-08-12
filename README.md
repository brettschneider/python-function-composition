# Function Composition In Python

The Single Responsibility Principle (SRP) emphasizes that a function, class, or module
should focus on a single task or responsibility. By adhering to SRP, code becomes more
modular and easier to understand, which in turn simplifies both maintenance and testing.
When each component is responsible for just one function, it reduces the risk of
unintended side effects, making debugging and writing test cases more straightforward.
SRP is a core part of the SOLID principles and aligns with other patterns like
Separation of Concerns, where different aspects of a program are managed independently,
and the Unix philosophy of "do one thing well." Following SRP allows developers to
create code that is cleaner, more maintainable, and easier to extend, laying a strong
foundation for robust software design.

Here's an example of a function that does not following SRP.  As you can see it's doing
multiple steps all in one function.

```python
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
```

The problem with this is, the function is doing too much.  This can make testing
unnecessarily difficult.  Additionally, if future request require similar functionality,
the code buried someone "in the middle" of this function cannot be reused.  Finally, as more
functionality is added to **this** request it will continue to become more complex and even
harder to test.

Here's some code that performs the exact same functionality, but each step has been
broken out into its own function.

```python
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
```

By breaking down the functionality into smaller, focused functions, testing becomes
significantly easier. Each function now has a single responsibility, allowing you to
test each one in isolation. For example, you can write unit tests specifically for
`create_filepath` to ensure it constructs the correct file path, or for
`parse_lines_to_dicts` to verify that it correctly parses JSON strings into
dictionaries. This approach not only simplifies the testing process but also makes the
codebase more flexible and resilient to change. If any step in the process needs to be
modified or extended, you can do so without affecting the other parts of the code,
minimizing the risk of introducing bugs. This modular design not only adheres to the
Single Responsibility Principle but also sets the stage for easier maintenance and
scalability as your application grows.

While the refactored version of the `get_people` function is more modular and easier to
test, the readability of the nested function calls can be unpleasant and challenging to
follow. The deeply nested structure can obscure the flow of logic, making it harder for
someone reading the code to quickly grasp what is happening at each step. This layering of
function calls can lead to confusion, particularly as the codebase evolves and more
complexity is introduced. Although each function is focused and well-defined, the overall
composition may feel cumbersome and detract from the clarity of the code. Finding a
balance between modularity and readability is essential, and the current approach, while
effective in isolation, can be difficult to maintain and understand when presented in
this nested format.

`get_people` _could_ be formatted in a slightly different way to make it more
readable, but it's still not ideal:

```python
@app.get('/api/people/{area}')
def get_people(area: str) -> list[Contact]:
    return convert_to_contacts(
        parse_dicts(
            read_lines(
                create_filepath(area)
            )
        )
    )
```

I've found an alternative syntatic technique that can make you code more elegant and
readable. Introducing the `@composable` decorator:

```python
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
```

The `@composable` decorator enhances code readability and maintainability by enabling function
chaining through the `|` operator. When applied to functions, this decorator allows them to be
composed together in a more intuitive and linear fashion. By using `|`, you can chain the
functions in a sequence, making the data flow and processing steps more explicit and easier to
follow. For instance, with the `@composable` decorator, the previously nested `get_people`
function can be written as a series of chained operations:

```python
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
    chain = create_filepath | read_lines | parse_dicts | convert_to_contacts
    return chain(area)
```

This approach not only improves readability by presenting the processing steps in a clear
and sequential manner but also retains the benefits of modular design. Each function remains
focused on a single responsibility, and the chaining syntax makes the overall logic of
`get_people` more transparent. The `@composable` decorator thus provides a powerful tool for
composing functions in a way that enhances both code clarity and maintainability.

By using the `@composable` decorator (think of it like a pipe operator that you'd use from
a shell prompt), each function in the refactored `get_people` implementation becomes highly
reusable and can be easily incorporated into other compositions within your FastAPI
application. This modular approach allows you to repurpose these functions for various tasks,
streamlining the development of new features and endpoints. For example, you might use
`create_filepath` and `read_file_lines` for different endpoints that need to process files,
or `parse_lines_to_dicts` and `convert_dicts_to_contacts` in other contexts where JSON data
needs to be handled. The clear, composable chaining syntax not only enhances readability but
also supports the creation of flexible and maintainable code that can adapt to evolving
requirements. As your application grows, this reusable design will facilitate the development
of complex functionality while keeping your codebase clean and well-organized.

As a bonus, since the `@composable` decorator overloads the `__ror__` dunder method, you can
use static values at the beginning of the chain, thus making your chains even more simple and
readable.

```python
@app.get('/api/people/{area}')
def get_people(area: str) -> list[Contact]:
    return area | create_filepath | read_lines | parse_dicts | convert_to_contacts
```

A full, runnable copy of the source code for this article can be found at
[https://github.com/brettschneider/python-function-composition](https://github.com/brettschneider/python-function-composition).