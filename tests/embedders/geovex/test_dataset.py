"""GeoVex HexagonalDataset tests."""
from contextlib import nullcontext as does_not_raise
from typing import TYPE_CHECKING, Any

import pandas as pd
import pytest

from srai.embedders.geovex.dataset import HexagonalDataset
from srai.h3 import get_local_ij_index
from srai.neighbourhoods import H3Neighbourhood

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


ROOT_REGION = "891e205194bffff"
RING_DISTANCE = 25


# @pytest.fixture  # type: ignore
def regions_data_df() -> pd.DataFrame:
    """Get example regions for testing."""
    neighbourhood = H3Neighbourhood()
    regions_indices = [ROOT_REGION]
    regions_indices.extend(
        list(neighbourhood.get_neighbours_up_to_distance(ROOT_REGION, RING_DISTANCE))
    )
    data_df = pd.DataFrame(
        list(range(len(regions_indices))), index=regions_indices, columns=["data"]
    )
    return data_df


@pytest.mark.parametrize(  # type: ignore
    "ring_distance,expectation",
    [
        (-1, pytest.raises(ValueError)),
        (0, pytest.raises(ValueError)),
        (1, pytest.raises(ValueError)),
        (2, does_not_raise()),
        (3, does_not_raise()),
    ],
)
def test_raises_with_incorrect_ring_distance(
    ring_distance: int, expectation: Any, mocker: "MockerFixture"
) -> None:
    """Test if HexagonalDataset checks ring_distance correctness."""
    data = pd.DataFrame()
    neighbourhood = mocker.Mock()
    with expectation:
        HexagonalDataset(data, neighbourhood, neighbor_k_ring=ring_distance)


@pytest.mark.parametrize("ring_distance", [2, 3, 4])  # type: ignore
def test_dataset_length(ring_distance: int, regions_data_df: pd.DataFrame):
    """Test if HexagonalDataset constructs lookup tables correctly."""
    neighbourhood: H3Neighbourhood = H3Neighbourhood(regions_data_df)
    dataset = HexagonalDataset(
        regions_data_df, neighbourhood, neighbor_k_ring=ring_distance
    )  # type: ignore
    assert len(dataset) == len(
        neighbourhood.get_neighbours_up_to_distance(
            ROOT_REGION, distance=RING_DISTANCE - ring_distance, include_center=True, unchecked=True
        )
    )


def test_dataset_item(regions_data_df: pd.DataFrame) -> None:
    """Test if HexagonalDataset constructs lookup tables correctly."""
    import numpy as np

    ring_distance = 2

    neighbourhood = H3Neighbourhood(regions_data_df)
    dataset = HexagonalDataset(
        regions_data_df, neighbourhood, neighbor_k_ring=ring_distance
    )  # type: ignore
    item = next(iter(dataset)).detach().numpy()
    # flatten it out and get the corresponding hexagons
    cells = regions_data_df.reset_index().set_index("data").loc[item.reshape(-1).tolist()].values

    # it starts with the root region
    # for each of the h3s, calculate the ij index
    ijs = np.array([get_local_ij_index(ROOT_REGION, _cell) for _cell in cells])

    ijs = ijs.reshape(ring_distance * 2 + 2, ring_distance * 2 + 2, 2)

    # commpare to the transposed image in the paper
    # specifically fig. 3
    # the bottom and right are padded by 0s for even #
    desired = np.array(
        [
            [(0, 0), (0, 0), (0, 2), (1, 2), (2, 2), (0, 0)],
            [(0, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (0, 0)],
            [(-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (0, 0)],
            [(-2, -1), (-1, -1), (0, -1), (1, -1), (0, 0), (0, 0)],
            [(-2, -2), (-1, -2), (0, -2), (0, 0), (0, 0), (0, 0)],
            [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)],
        ]
    )
    assert np.all(ijs.transpose(1, 0, -1) == desired)


if __name__ == "__main__":
    test_dataset_item(regions_data_df())
