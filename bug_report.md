# Bug Report (Part 7)

I put each bug into `app/routers/artworks.py` one at a time, ran `pytest`, wrote down what failed, and then undid it before trying the next one.

| Bug | Test(s) that failed |
| --- | --- |
| 1 | `test_create_artwork` failed (got 200 instead of 201). These 6 also errored, because my `created_artwork` fixture checks for a 201: `test_create_artwork_is_saved`, `test_create_duplicate`, `test_create_duplicate_ignores_case`, `test_update_artwork`, `test_update_same_title_and_artist_is_allowed`, `test_delete_artwork` |
| 2 | `test_create_duplicate_ignores_case` (got 201 instead of 409) |
| 3 | `test_update_same_title_and_artist_is_allowed` (got 409 instead of 200) |
| 4 | `test_delete_artwork` (the GET afterward was 200 instead of 404, so it never really deleted) |
| 5 | `test_filter_by_artist[lowercase-partial]` and `test_filter_by_artist[partial-middle-of-name]` |

## Notes

- Bug 1 broke a lot of tests at once because so many of them use `created_artwork`. The ones that show ERROR instead of FAILED broke during setup (in the fixture), not in the test itself.
- Bug 5 only got caught because my filter cases search for "monet" and "da vinci", which come in the middle of the name. If I had only tested "Claude Monet" it would have passed, because that's the start of the name.
- Every bug got caught by at least one test, so I didn't have to add any new tests for gaps.

After undoing all 5 bugs I ran `pytest` again and everything passed (40 passed).
