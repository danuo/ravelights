def test_available_generators(ravelights_app):
    keys = ["pattern", "vfilter", "thinner", "dimmer", "effect"]
    avail_gens = ravelights_app.meta_handler.api_content["available_generators"]
    for k in keys:
        assert k in avail_gens
        assert len(avail_gens[k]) > 0


def test_keywords(ravelights_app):
    avail_keywords = ravelights_app.meta_handler.api_content["available_keywords"]
    assert "short" in avail_keywords
    assert "ambient" in avail_keywords
