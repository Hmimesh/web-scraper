from transliteration import basic_transliterate


def test_basic_digraph_transliteration():
    assert basic_transliterate("Noor") == "נור"
    assert basic_transliterate("Lee") == "לי"
    assert basic_transliterate("Gail") == "גייל"
    assert basic_transliterate("Schneider") == "שניידר"
