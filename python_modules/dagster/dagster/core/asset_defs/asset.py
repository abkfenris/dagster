from typing import AbstractSet, Mapping, Optional

from dagster import check
from dagster.core.definitions import OpDefinition
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.partition import PartitionsDefinition

from .partition_mapping import PartitionMapping


class AssetsDefinition:
    def __init__(
        self,
        input_names_by_asset_key: Mapping[AssetKey, str],
        output_names_by_asset_key: Mapping[AssetKey, str],
        op: OpDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        can_subset: bool = False,
        subset=None,
    ):
        self._op = op
        self._a = input_names_by_asset_key
        self._b = output_names_by_asset_key
        self._input_defs_by_asset_key = {
            asset_key: op.input_dict[input_name]
            for asset_key, input_name in input_names_by_asset_key.items()
        }

        self._output_defs_by_asset_key = {
            asset_key: op.output_dict[output_name]
            for asset_key, output_name in output_names_by_asset_key.items()
        }
        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}
        self._can_subset = can_subset
        self._subset = subset

    @property
    def can_subset(self) -> bool:
        return self._can_subset

    @property
    def op(self) -> OpDefinition:
        return self._op

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        if self._subset is None:
            return self._output_defs_by_asset_key.keys()
        return self._subset

    @property
    def output_defs_by_asset_key(self):
        return self._output_defs_by_asset_key

    @property
    def input_defs_by_asset_key(self):
        return self._input_defs_by_asset_key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._partitions_def

    def subset(self, asset_keys: AbstractSet[AssetKey]) -> "AssetsDefinition":
        if not self.can_subset:
            raise "TODO"
        assert asset_keys <= self.asset_keys
        # gross
        import copy
        import hashlib

        nn = hashlib.md5(str(sorted(asset_keys)).encode()).hexdigest()[:5]

        new_op = copy.copy(self.op)
        new_op._name = f"{new_op.name}_{nn}"
        new_op._output_defs = [self.output_defs_by_asset_key[ak] for ak in asset_keys]
        return AssetsDefinition(
            self._a,
            self._b,
            new_op,
            self.partitions_def,
            self._partition_mappings,
            self.can_subset,
            asset_keys,
        )

    def upstream_assets(self, asset_key) -> AbstractSet[AssetKey]:
        output_def = self.output_defs_by_asset_key[asset_key]
        asset_deps = (output_def.metadata or {}).get(".dagster/asset_deps")
        if asset_deps is not None:
            return asset_deps
        # if no deps specified, assume depends on all inputs and no outputs
        return set(self.input_defs_by_asset_key.keys())

    def get_partition_mapping(self, in_asset_key: AssetKey) -> PartitionMapping:
        if self._partitions_def is None:
            check.failed("Asset is not partitioned")

        return self._partition_mappings.get(
            in_asset_key,
            self._partitions_def.get_default_partition_mapping(),
        )
