#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import unittest
from typing import cast

import torch
from torchrec.distributed.embeddingbag import (
    EmbeddingBagCollectionSharder,
)
from torchrec.distributed.planner.enumerators import EmbeddingEnumerator
from torchrec.distributed.planner.shard_estimators import EmbeddingPerfEstimator
from torchrec.distributed.planner.types import Topology
from torchrec.distributed.test_utils.test_model import TestSparseNN
from torchrec.distributed.types import ModuleSharder
from torchrec.modules.embedding_configs import EmbeddingBagConfig


class TestEmbeddingPerfEstimator(unittest.TestCase):
    def setUp(self) -> None:
        topology = Topology(world_size=2, compute_device="cuda")
        self.estimator = EmbeddingPerfEstimator(topology=topology)
        self.enumerator = EmbeddingEnumerator(
            topology=topology, estimator=self.estimator
        )

    def test_1_table_perf(self) -> None:
        tables = [
            EmbeddingBagConfig(
                num_embeddings=100,
                embedding_dim=10,
                name="table_0",
                feature_names=["feature_0"],
            )
        ]
        model = TestSparseNN(tables=tables, weighted_tables=[])
        sharding_options = self.enumerator.enumerate(
            module=model,
            sharders=[
                cast(ModuleSharder[torch.nn.Module], EmbeddingBagCollectionSharder())
            ],
        )

        expected_perfs = {
            ("dense", "data_parallel"): [0.000771545650929018, 0.000771545650929018],
            ("batched_dense", "data_parallel"): [
                0.0006239009873657056,
                0.0006239009873657056,
            ],
            ("dense", "table_wise"): [0.002933957239191402],
            ("batched_dense", "table_wise"): [0.0020919170400902315],
            ("batched_fused", "table_wise"): [0.0011095368078055323],
            ("sparse", "table_wise"): [0.002933957239191402],
            ("batched_fused_uvm", "table_wise"): [1.7279606239468448],
            ("batched_fused_uvm_caching", "table_wise"): [0.4003065699993969],
            ("dense", "row_wise"): [0.0010086863943489708, 0.0010086863943489708],
            ("batched_dense", "row_wise"): [
                0.0007442274487005296,
                0.0007442274487005296,
            ],
            ("batched_fused", "row_wise"): [
                0.00043569201211068144,
                0.00043569201211068144,
            ],
            ("sparse", "row_wise"): [0.0010086863943489708, 0.0010086863943489708],
            ("batched_fused_uvm", "row_wise"): [0.5427865421070772, 0.5427865421070772],
            ("batched_fused_uvm_caching", "row_wise"): [
                0.12581121044522733,
                0.12581121044522733,
            ],
            ("dense", "column_wise"): [0.002933957239191402],
            ("batched_dense", "column_wise"): [0.0020919170400902315],
            ("batched_fused", "column_wise"): [0.0011095368078055323],
            ("sparse", "column_wise"): [0.002933957239191402],
            ("batched_fused_uvm", "column_wise"): [1.7279606239468448],
            ("batched_fused_uvm_caching", "column_wise"): [0.4003065699993969],
            ("dense", "table_column_wise"): [0.002933957239191402],
            ("batched_dense", "table_column_wise"): [0.0020919170400902315],
            ("batched_fused", "table_column_wise"): [0.0011095368078055323],
            ("sparse", "table_column_wise"): [0.002933957239191402],
            ("batched_fused_uvm", "table_column_wise"): [1.7279606239468448],
            ("batched_fused_uvm_caching", "table_column_wise"): [0.4003065699993969],
            ("dense", "table_row_wise"): [0.0010086863943489708, 0.0010086863943489708],
            ("batched_dense", "table_row_wise"): [
                0.0007442274487005296,
                0.0007442274487005296,
            ],
            ("batched_fused", "table_row_wise"): [
                0.00043569201211068144,
                0.00043569201211068144,
            ],
            ("sparse", "table_row_wise"): [
                0.0010086863943489708,
                0.0010086863943489708,
            ],
            ("batched_fused_uvm", "table_row_wise"): [
                0.5427865421070772,
                0.5427865421070772,
            ],
            ("batched_fused_uvm_caching", "table_row_wise"): [
                0.12581121044522733,
                0.12581121044522733,
            ],
        }

        perfs = {
            (
                sharding_option.compute_kernel,
                sharding_option.sharding_type,
            ): [shard.perf for shard in sharding_option.shards]
            for sharding_option in sharding_options
        }

        self.assertEqual(expected_perfs, perfs)
