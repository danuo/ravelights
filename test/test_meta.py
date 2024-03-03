def test_available_generators(app_1):
    keys = ["pattern", "vfilter", "thinner", "dimmer", "effect"]
    avail_gens = app_1.meta_handler.api_content["available_generators"]
    for k in keys:
        assert k in avail_gens
        assert len(avail_gens[k]) > 0


def test_keywords(app_1):
    avail_keywords = app_1.meta_handler.api_content["available_keywords"]
    assert "short" in avail_keywords
    assert "ambient" in avail_keywords
