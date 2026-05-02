from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from arabic_morph_mi.data import Item


def check_split(y: np.ndarray, train: np.ndarray, test: np.ndarray) -> None:
    n_classes = int(y.max()) + 1
    train_counts = np.bincount(y[train], minlength=n_classes)
    test_counts = np.bincount(y[test], minlength=n_classes)
    if np.any(train_counts == 0) or np.any(test_counts == 0):
        raise ValueError(
            "Every class must appear in train and test. "
            f"train_counts={train_counts.tolist()} test_counts={test_counts.tolist()}"
        )


def random_split(y: list[int], test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    y_arr = np.asarray(y)
    idx = np.arange(len(y_arr))
    train, test = train_test_split(idx, test_size=test_size, stratify=y_arr, random_state=seed)
    check_split(y_arr, train, test)
    return train, test


def one_per_label_test_split(y: list[int], seed: int) -> tuple[np.ndarray, np.ndarray]:
    y_arr = np.asarray(y)
    rng = np.random.default_rng(seed)
    test = []
    for label in sorted(set(y)):
        candidates = np.where(y_arr == label)[0]
        if len(candidates) < 2:
            raise ValueError("Each label needs at least two examples.")
        test.append(int(rng.choice(candidates)))
    test_arr = np.array(sorted(test))
    train_arr = np.array([i for i in range(len(y_arr)) if i not in set(test_arr)])
    check_split(y_arr, train_arr, test_arr)
    return train_arr, test_arr


def heldout_root_split(items: list[Item], y: list[int], test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    y_arr = np.asarray(y)
    roots = sorted({item.root for item in items})
    n_test_roots = max(1, round(len(roots) * test_size))
    rng = np.random.default_rng(seed)

    for _ in range(2000):
        test_roots = set(rng.choice(roots, size=n_test_roots, replace=False).tolist())
        train = np.array([i for i, item in enumerate(items) if item.root not in test_roots])
        test = np.array([i for i, item in enumerate(items) if item.root in test_roots])
        try:
            check_split(y_arr, train, test)
        except ValueError:
            continue
        return train, test

    raise ValueError("Could not make a held-out-root split with all classes in train and test.")


def heldout_template_split(items: list[Item], y: list[int], test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    y_arr = np.asarray(y)
    templates = sorted({item.template for item in items})
    n_test_templates = max(1, round(len(templates) * test_size))
    rng = np.random.default_rng(seed)

    for _ in range(2000):
        test_templates = set(rng.choice(templates, size=n_test_templates, replace=False).tolist())
        train = np.array([i for i, item in enumerate(items) if item.template not in test_templates])
        test = np.array([i for i, item in enumerate(items) if item.template in test_templates])
        try:
            check_split(y_arr, train, test)
        except ValueError:
            continue
        return train, test

    raise ValueError("Could not make a held-out-template split with all classes in train and test.")
