def test_home_and_explorer_pages_render(client):
    for path in ("/", "/destinations", "/hotels", "/food"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"YatraGo" in response.data


def test_missing_page_uses_friendly_not_found_template(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"We can" in response.data


def test_food_explorer_filters_by_region_and_city(client):
    response = client.get("/food?region=Telangana&city=Hyderabad")
    assert response.status_code == 200
    assert b"Hyderabadi Biryani" in response.data
    assert b"Masala Dosa" not in response.data
