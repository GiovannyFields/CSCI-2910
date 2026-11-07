import pytest

# These have to match the messages in app/routers/artworks.py exactly
NOT_FOUND_MESSAGE = "Artwork not found"
DUPLICATE_MESSAGE = "An artwork with that title and artist already exists"


# GET /artworks/  (getting the whole list)
def test_list_artworks_empty(client):
    """
    No seeded_db here, so the table should be empty.

    - Should get **200** and an empty list back
    """
    response = client.get("/artworks/")

    assert response.status_code == 200
    assert response.json() == []


# There are 11 seeded artworks and the default limit is 10.
# I check the ids too and not just how many came back, so I know skip
# actually skipped the right ones.
@pytest.mark.parametrize(
    "params, expected_ids",
    [
        ({}, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ({"limit": 3}, [1, 2, 3]),
        ({"limit": 0}, []),
        ({"limit": 100}, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
        ({"skip": 8}, [9, 10, 11]),
        ({"skip": 4, "limit": 2}, [5, 6]),
        ({"skip": 20}, []),
    ],
    ids=[
        "default-is-10",
        "limit-3",
        "limit-0",
        "limit-100-gets-all-11",
        "skip-8",
        "skip-4-limit-2",
        "skip-past-the-end",
    ],
)
def test_pagination_counts(client, seeded_db, params, expected_ids):
    response = client.get("/artworks/", params=params)

    assert response.status_code == 200
    artworks = response.json()
    assert len(artworks) == len(expected_ids)

    ids_we_got = []
    for artwork in artworks:
        ids_we_got.append(artwork["id"])
    assert ids_we_got == expected_ids


# The router says skip >= 0 and limit has to be between 0 and 100
@pytest.mark.parametrize(
    "params, bad_param",
    [
        ({"skip": -1}, "skip"),
        ({"limit": -1}, "limit"),
        ({"limit": 101}, "limit"),
        ({"limit": "ten"}, "limit"),
    ],
    ids=["negative-skip", "negative-limit", "limit-over-100", "limit-not-a-number"],
)
def test_pagination_invalid(client, seeded_db, params, bad_param):
    response = client.get("/artworks/", params=params)

    assert response.status_code == 422
    # make sure the error is about the param we messed up
    assert response.json()["detail"][0]["loc"] == ["query", bad_param]


MONET_TITLES = [
    "Impression, Sunrise",
    "Woman with a Parasol – Madame Monet and Her Son",
]


# "monet" and "da vinci" are in the MIDDLE of the artist name, so these
# only pass if the filter matches anywhere in the name (not just the start)
@pytest.mark.parametrize(
    "artist, expected_titles",
    [
        ("Claude Monet", MONET_TITLES),
        ("monet", MONET_TITLES),
        ("da vinci", ["Mona Lisa", "Lady with an Ermine"]),
        ("Gustav Klimt", []),
    ],
    ids=["exact", "lowercase-partial", "partial-middle-of-name", "no-match"],
)
def test_filter_by_artist(client, seeded_db, artist, expected_titles):
    response = client.get("/artworks/", params={"artist": artist})

    assert response.status_code == 200

    titles = []
    for artwork in response.json():
        titles.append(artwork["title"])
    assert titles == expected_titles


# GET /artworks/{id}  (getting one artwork)
def test_get_seeded_artwork(client, seeded_db):
    # Arrange: seeded_db has already loaded the 11 artworks (the Mona Lisa is first)
    expected = {"id": 1, **seeded_db[0]}

    # Act
    response = client.get("/artworks/1")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


# PUT needs a body or FastAPI gives a 422 before it ever looks for artwork 9999
@pytest.mark.parametrize(
    "method, use_body",
    [
        ("get", False),
        ("put", True),
        ("delete", False),
    ],
    ids=["get", "put", "delete"],
)
def test_artwork_not_found(client, sample_artwork, method, use_body):
    kwargs = {"json": sample_artwork} if use_body else {}
    response = client.request(method, "/artworks/9999", **kwargs)

    assert response.status_code == 404
    # checking the message proves the 404 came from the router and not a typo in the URL
    assert response.json() == {"detail": NOT_FOUND_MESSAGE}


def test_non_integer_id(client, seeded_db):
    """
    The id has to be an int, so a word should get rejected by FastAPI.

    - Should get **422**
    """
    response = client.get("/artworks/mona-lisa")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "artwork_id"]


# POST /artworks/  (creating)
def test_create_artwork(client, sample_artwork):
    """
    POST The Kiss and check what comes back.

    - Should get **201**, a new int id, and every field I sent
    """
    response = client.post("/artworks/", json=sample_artwork)

    assert response.status_code == 201
    new_artwork = response.json()
    assert isinstance(new_artwork["id"], int)
    assert new_artwork["title"] == sample_artwork["title"]
    assert new_artwork["artist"] == sample_artwork["artist"]
    assert new_artwork["year"] == sample_artwork["year"]
    assert new_artwork["medium"] == sample_artwork["medium"]
    assert new_artwork["museum"] == sample_artwork["museum"]
    assert new_artwork["image_url"] == sample_artwork["image_url"]


def test_create_artwork_is_saved(client, created_artwork):
    """
    The test above proves the API SAID it saved it. This one GETs it back
    to prove it really is in the database.
    """
    response = client.get(f"/artworks/{created_artwork['id']}")

    assert response.status_code == 200
    assert response.json() == created_artwork


def test_create_duplicate(client, sample_artwork, created_artwork):
    """
    created_artwork already POSTed The Kiss, so posting it again should fail.

    - Should get **409** with the duplicate message
    """
    response = client.post("/artworks/", json=sample_artwork)

    assert response.status_code == 409
    assert response.json() == {"detail": DUPLICATE_MESSAGE}


def test_create_duplicate_ignores_case(client, sample_artwork, created_artwork):
    """
    Same thing but "THE KISS" by "gustav klimt". The README says the
    duplicate check ignores case, so this should still be a **409**.
    """
    different_case = sample_artwork.copy()
    different_case["title"] = sample_artwork["title"].upper()
    different_case["artist"] = sample_artwork["artist"].lower()

    response = client.post("/artworks/", json=different_case)

    assert response.status_code == 409
    assert response.json() == {"detail": DUPLICATE_MESSAGE}


# Take out one field at a time. Every field is required so all of these are 422.
@pytest.mark.parametrize(
    "missing_field",
    ["title", "artist", "year", "medium", "museum", "image_url"],
)
def test_create_missing_field(client, sample_artwork, missing_field):
    body = sample_artwork.copy()
    del body[missing_field]

    response = client.post("/artworks/", json=body)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", missing_field]


# One bad value at a time. These rules come from app/schemas.py
@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("year", 3000),
        ("year", "nineteen-oh-seven"),
        ("title", ""),
        ("artist", ""),
    ],
    ids=["future-year", "year-not-int", "empty-title", "empty-artist"],
)
def test_create_invalid_value(client, sample_artwork, field, bad_value):
    body = sample_artwork.copy()
    body[field] = bad_value

    response = client.post("/artworks/", json=body)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]
    # and nothing should have been saved
    assert client.get("/artworks/").json() == []


# PUT /artworks/{id}  (updating)
def test_update_artwork(client, created_artwork, updated_artwork):
    """
    Change The Kiss into The Scream.

    - Should get **200** and the new data back
    - Then GET it again to make sure it actually saved and wasn't just echoed back
    """
    artwork_id = created_artwork["id"]
    expected = {"id": artwork_id, **updated_artwork}

    response = client.put(f"/artworks/{artwork_id}", json=updated_artwork)

    assert response.status_code == 200
    assert response.json() == expected

    check = client.get(f"/artworks/{artwork_id}")
    assert check.json() == expected


def test_update_into_duplicate(client, seeded_db):
    """
    Try to turn artwork 2 (Lady with an Ermine) into a second Mona Lisa.

    - Should get **409**
    - Artwork 2 should still be Lady with an Ermine afterward
    """
    mona_lisa = seeded_db[0]
    lady_with_an_ermine = seeded_db[1]

    body = lady_with_an_ermine.copy()
    body["title"] = mona_lisa["title"]
    body["artist"] = mona_lisa["artist"]

    response = client.put("/artworks/2", json=body)

    assert response.status_code == 409
    assert response.json() == {"detail": DUPLICATE_MESSAGE}

    check = client.get("/artworks/2")
    assert check.json() == {"id": 2, **lady_with_an_ermine}


def test_update_same_title_and_artist_is_allowed(client, created_artwork):
    """
    Keep the same title and artist but change the museum.
    An artwork can't be a duplicate of itself, so this should be **200** not 409.
    """
    artwork_id = created_artwork["id"]

    body = created_artwork.copy()
    del body["id"]
    body["museum"] = "Upper Belvedere, Vienna"

    response = client.put(f"/artworks/{artwork_id}", json=body)

    assert response.status_code == 200
    assert response.json()["museum"] == "Upper Belvedere, Vienna"

    check = client.get(f"/artworks/{artwork_id}")
    assert check.json() == {"id": artwork_id, **body}


# DELETE /artworks/{id}
def test_delete_artwork(client, created_artwork):
    """
    Delete The Kiss.

    - Should get **204** with an empty body
    - Then a GET should be **404** since it's gone
    """
    artwork_id = created_artwork["id"]

    response = client.delete(f"/artworks/{artwork_id}")

    assert response.status_code == 204
    assert response.content == b""

    check = client.get(f"/artworks/{artwork_id}")
    assert check.status_code == 404
    assert check.json() == {"detail": NOT_FOUND_MESSAGE}
