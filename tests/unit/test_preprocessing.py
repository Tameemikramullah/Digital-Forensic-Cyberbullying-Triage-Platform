from ml.preprocessing.cleaner import clean_text


def test_clean_text_normalises_urls_mentions_and_preserves_hashtag_words():
    text = "@User THIS is #Abuse! https://example.test/x"
    assert clean_text(text) == "usertoken this is abuse urltoken"
