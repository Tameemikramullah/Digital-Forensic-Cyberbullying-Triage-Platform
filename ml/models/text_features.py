"""Feature builders shared by the classical cyberbullying classifiers."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion


def build_social_media_features() -> FeatureUnion:
    """Combine semantic word features with robust character n-grams.

    Character features retain useful signals from spelling variation, slurs,
    abbreviations and obfuscation that are common in social-media evidence.
    """
    return FeatureUnion([
        ("word", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.98,
            sublinear_tf=True,
            strip_accents="unicode",
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
            max_features=120_000,
            sublinear_tf=True,
        )),
    ])
