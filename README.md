# Lab 6 - Testing the Art API

The Art API was already finished. My job was to write pytest tests for it instead of testing it by hand on `/docs` like last lab.

## What I wrote

- `tests/conftest.py` - fixtures: an in-memory test database (so the tests never touch `artworks.db`), the client, and my `sample_artwork`, `updated_artwork`, and `created_artwork` fixtures
- `tests/test_basics.py` - my first test (1 + 1 == 2)
- `tests/test_artworks.py` - happy path, unhappy path, and parametrized tests for `/artworks`
- `bug_report.md` - which tests caught each bug in Part 7

40 tests, all passing.

## How to run it

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

The server doesn't need to be running for the tests.

## What I learned

- Check the result, not just the status code. If the code were broken, would the test fail?
- 422s come from FastAPI automatically, but 404 and 409 come from the router code, so that's where bugs can hide.
- Parametrize instead of copy-pasting tests, and use `ids=` so the names make sense.
