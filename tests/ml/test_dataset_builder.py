"""
Unit Tests for RAVEN ML Dataset Builder
"""

from ml.dataset import MLDatasetBuilder


def test_dataset_builder_from_simulator():
    builder = MLDatasetBuilder(seed=42)
    dataset = builder.build_dataset_from_simulator()

    assert dataset.metadata.sample_count > 0
    assert dataset.metadata.dataset_hash != ""
    assert len(dataset.feature_names) == 9

    total_split_count = (
        len(dataset.train_split.target_vector)
        + len(dataset.val_split.target_vector)
        + len(dataset.test_split.target_vector)
    )
    assert total_split_count == dataset.metadata.sample_count
