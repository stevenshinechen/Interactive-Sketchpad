from enum import StrEnum

from datasets import Dataset, load_dataset


class IsobenchTask(StrEnum):
    CHEMISTRY = "chemistry"
    GRAPH_CONNECTIVITY = "graph_connectivity"
    GRAPH_ISOMORPHISM = "graph_isomorphism"
    GRAPH_MAXFLOW = "graph_maxflow"
    MATH_BREAKPOINT = "math_breakpoint"
    MATH_CONVEXITY = "math_convexity"
    MATH_PARITY = "math_parity"
    PHYSICS = "physics"
    PUZZLE = "puzzle"
    WINNER_ID = "winner_id"


ISOBENCH_PATH = "isobench/IsoBench"


def load_isobench_dataset(task: IsobenchTask) -> Dataset:
    ds = load_dataset(ISOBENCH_PATH, task)
    validation_data = ds["validation"]
    return validation_data


if __name__ == "__main__":
    for task in IsobenchTask:
        print(task)
        ds = load_isobench_dataset(task)
        print(ds)
        for data in ds.select(range(2)):
            print(data)
            print("\n\n")
        print("\n\n")
