import numpy as np

from src import config
from src.event_intelligence.clustering import cluster_embeddings


def test_clustering_runs_on_small_embedding_matrix():
    rng = np.random.default_rng(config.RANDOM_SEED)
    embeddings = rng.normal(size=(20, 8)).astype("float32")
    labels = cluster_embeddings(embeddings, algorithm="agglomerative")
    assert len(labels) == 20
