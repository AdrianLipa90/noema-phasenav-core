from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .git_object_vectorization import GitRepositorySnapshot

PRIVATE_REPOSITORY_SNAPSHOT_VERSION = "0.9.0"


@dataclass(frozen=True)
class PrivateRepositoryHead:
    repository: str
    repository_id: int
    default_branch: str
    archived: bool
    head_commit: str | None

    @property
    def status(self) -> str:
        if self.head_commit is None:
            return "ARCHIVED_EMPTY_SOURCE" if self.archived else "UNBORN_EMPTY_SOURCE"
        return "ARCHIVED_HEAD_PRESENT" if self.archived else "HEAD_PRESENT"

    def vector_receipt(self) -> dict[str, object] | None:
        if self.head_commit is None:
            return None
        return GitRepositorySnapshot.from_head(
            self.repository,
            self.repository_id,
            self.default_branch,
            self.head_commit,
        ).receipt()


PRIVATE_REPOSITORY_HEADS = (
    PrivateRepositoryHead('AdrianLipa90/ideal-winner', 996239703, 'main', False, '2071939a111a72f1a84b1898a7090b709d99ad73'),
    PrivateRepositoryHead('AdrianLipa90/CIEL-Omega-GQC', 1087439961, 'main', False, '11c30d3380966bbaa86647205bc634de843cd477'),
    PrivateRepositoryHead('AdrianLipa90/CielOmegaNew', 1110243681, 'main', False, '4bcf609a24475d7b894be0c084722e5b79196ee1'),
    PrivateRepositoryHead('AdrianLipa90/ciel-old', 1126072231, 'old', False, 'a448718a8fab4b80fddf7c4fb806653b9e48a645'),
    PrivateRepositoryHead('AdrianLipa90/Informational-Dynamics-of-Metatime', 1189464427, 'main', False, '85f2636f34d2928254baf8d0426c5ddd7ebcacd3'),
    PrivateRepositoryHead('AdrianLipa90/Research-various-data', 1193856852, 'main', False, '569993a8f5f07238a6df57eb7a1bb20298a51e9f'),
    PrivateRepositoryHead('AdrianLipa90/CIEL-The-Living-Core', 1194697607, 'main', False, '90e12206c29c231f2704156be09bed7a388af902'),
    PrivateRepositoryHead('AdrianLipa90/SapiensOrbital', 1194730471, 'main', False, '927cd00de051376d6dc9a771179b7556484ad3a5'),
    PrivateRepositoryHead('AdrianLipa90/LVUT', 1195627863, 'main', False, '8cff28b5df1ec56eeb796e4dbde78c1638cbba9f'),
    PrivateRepositoryHead('AdrianLipa90/VivOS', 1195782543, 'main', False, 'c6563e5d77dc7f24ecfc4c87f2f67820213dbed8'),
    PrivateRepositoryHead('AdrianLipa90/ApocalyptOS', 1197679127, 'main', False, 'a9adb7102d7289730479b959bac2142231afb59d'),
    PrivateRepositoryHead('AdrianLipa90/LVUT-ValidatOR', 1197871953, 'main', False, '21645040dad3ed747e966607a9fc0cdb895cf986'),
    PrivateRepositoryHead('AdrianLipa90/Orbital-System-base', 1200655989, 'main', False, '45735e8b16850374074b6ea3e1f99ca3dc8d4e2a'),
    PrivateRepositoryHead('AdrianLipa90/CiEL-Website', 1205857897, 'main', False, '099b5ddf8a1649eb600beb8beead690620e708fd'),
    PrivateRepositoryHead('AdrianLipa90/Crime-in-relations', 1212745882, 'main', False, 'fa012cc57a5d87fe6aeae49350ff722a143c014c'),
    PrivateRepositoryHead('AdrianLipa90/Ciel-Semantic-Model-', 1222779303, 'main', False, '3cafdfd0e93802aa6bd5d560eb61ce774f5cb2a4'),
    PrivateRepositoryHead('AdrianLipa90/Technodemocracy-Law', 1278591859, 'master', False, 'ce7e3b99e2f26b6504dfecb15a950559769120cf'),
    PrivateRepositoryHead('AdrianLipa90/cielingo-canon', 1287208353, 'main', False, '533f6f01f5e509213bd5a52ef4227cd9d3f44975'),
    PrivateRepositoryHead('AdrianLipa90/noema-poincyre-cymatix', 1287238577, 'main', True, None),
    PrivateRepositoryHead('AdrianLipa90/noema-poincare-cymatix', 1287240928, 'main', False, '02b4ff48c31dd872d152911cd908732a6b75b583'),
    PrivateRepositoryHead('AdrianLipa90/noema-system-index', 1289542895, 'master', False, '3ec568ce3e73c4f42254ab153934e45a56c7df51'),
    PrivateRepositoryHead('AdrianLipa90/noema-identity-chain', 1289542931, 'master', False, '904ec8cc672bd7938dea9ea9355af784ebb81bad'),
    PrivateRepositoryHead('AdrianLipa90/noema-surface', 1289542953, 'master', False, '9bec01ffdb233d024b692b053b6b8857ca979071'),
    PrivateRepositoryHead('AdrianLipa90/noema-phasenav-core', 1289542983, 'master', False, '611c4e0ac75d02d3386c15bd8744e5e9e98ccb78'),
    PrivateRepositoryHead('AdrianLipa90/noema-orbital-memory', 1289543026, 'master', False, 'd83fce6c3a0aeee6fbc367a18b6b0b742d451b12'),
    PrivateRepositoryHead('AdrianLipa90/noema-memory-lanes', 1289543060, 'master', False, '0c1c7bf3e32c82ab550ecdf5730362ee533603b1'),
    PrivateRepositoryHead('AdrianLipa90/noema-tripod-runtime', 1289543083, 'master', False, '24d7686f2c99f8625bd6be3cc4c7cbd1edf64edd'),
    PrivateRepositoryHead('AdrianLipa90/noema-runtime-daemons', 1289543119, 'master', False, '640d4db17b57fd7d39edf42df1bdad53214e4654'),
    PrivateRepositoryHead('AdrianLipa90/noema-ciel-telekom', 1289543146, 'master', False, '6cdc1f2d6815324990fba9eaf0b178d01357f264'),
    PrivateRepositoryHead('AdrianLipa90/noema-surface-mcp', 1289543175, 'master', False, '90e9587c488d8bd33d98bad986316bb9c289ba3c'),
    PrivateRepositoryHead('AdrianLipa90/noema-holonomic-doctor', 1289543194, 'master', False, 'b9636b58b0bc03410a2e166e171aebb73a791462'),
    PrivateRepositoryHead('AdrianLipa90/noema-research-canon', 1289543221, 'master', False, '58e127789190a86bae8dbc26088728ab5f3c3d87'),
    PrivateRepositoryHead('AdrianLipa90/opencode', 1289581635, 'dev', False, '1b9b2604581bfdac263a69a2d5846bd2a91da6cc'),
    PrivateRepositoryHead('AdrianLipa90/buildroot', 1289581637, 'master', False, 'c5728ff5af9898ab1db967d7e13af2b17825ed25'),
    PrivateRepositoryHead('AdrianLipa90/NOEMA-vectorised-full', 1293508344, 'master', False, '205ea2937dce04124753feb46f91266d228564d9'),
    PrivateRepositoryHead('AdrianLipa90/ciel-apocalyptos', 1298629932, 'main', False, '142d92826787305988285b9d6b2269c24b581368'),
    PrivateRepositoryHead('AdrianLipa90/Origins-DNA', 1300841535, 'main', False, 'b50627124f70b06905a9c059c92a133fa6d089cb'),
    PrivateRepositoryHead('AdrianLipa90/CIEL-NOEMA-HTRI-CIELingo-Phasenav', 1324385060, 'main', False, '4d47a628e24f02e14496cf34686ff347a9135f28'),
    PrivateRepositoryHead('AdrianLipa90/CIELfeatOAIDev', 1324490678, 'main', False, 'a36797477e0d17a73095119593885dd494b9e3d4'),
    PrivateRepositoryHead('AdrianLipa90/PhaseNav-MAS-Upgrade', 1324827908, 'main', False, '6792f5ae0d7861fc3ed752ff61d5915e0290979f'),
)

EXPECTED_REPOSITORY_COUNT = 40
EXPECTED_HEAD_PRESENT_COUNT = 39
EXPECTED_INVENTORY_SHA256 = 'd47ace603e52fdb3fbe77556b370ac272d4ac5f3d0232b0bda4fbc998a05ab70'
EXPECTED_VECTOR_SET_SHA256 = 'a7e458063b3fb94d817f132c3c4dceee5a6ed7ade32237bec4acaff392640e0b'


def build_private_repository_snapshot() -> dict[str, object]:
    rows = []
    vector_pairs = []
    for record in PRIVATE_REPOSITORY_HEADS:
        vector = record.vector_receipt()
        row = {
            "repository": record.repository,
            "repository_id": record.repository_id,
            "default_branch": record.default_branch,
            "archived": record.archived,
            "head_commit": record.head_commit,
            "status": record.status,
            "vector_sha256": None if vector is None else vector["head_vector_sha256"],
        }
        rows.append(row)
        if vector is not None:
            vector_pairs.append((record.head_commit, vector["head_vector_sha256"]))

    inventory_rows = [
        {
            "repository": row["repository"],
            "repository_id": row["repository_id"],
            "default_branch": row["default_branch"],
            "archived": row["archived"],
            "head_commit": row["head_commit"],
            "status": row["status"],
        }
        for row in rows
    ]
    inventory_sha = hashlib.sha256(
        json.dumps(inventory_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    vector_set_sha = hashlib.sha256(
        json.dumps(vector_pairs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "phasenav.private-repository-head-snapshot/v0.9",
        "version": PRIVATE_REPOSITORY_SNAPSHOT_VERSION,
        "scope": {
            "owner": "AdrianLipa90",
            "visibility": "private",
            "selection": "all visible private repositories; archived retained",
        },
        "repository_count": len(rows),
        "head_present_count": len(vector_pairs),
        "inventory_sha256": inventory_sha,
        "vector_set_sha256": vector_set_sha,
        "repositories": rows,
        "vectorization": {
            "parent": "native_git_object_digest_only",
            "routing_dimension": 36,
            "repository_name_vector_parent": False,
            "repository_id_vector_parent": False,
            "default_branch_vector_parent": False,
            "path_label_vector_parent": False,
            "size_vector_parent": False,
            "collatz_string_hash_used": False,
            "scientific_promotion": "NOT_PERFORMED",
        },
    }


PRIVATE_REPOSITORY_SNAPSHOT = build_private_repository_snapshot()
