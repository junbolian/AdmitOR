# IR: {"sets":{"N":["A","B","C","D","E"],"L":[["A","B"],["A","C"],["A","E"],["B","A"],["B","C"],["B","D"],["B","E"],["C","A"],["C","D"],["C","E"],["D","A"],["D","B"],["D","C"],["D","E"],["E","B"],["E","D"]],"F":"arcs (u,v) in L with bandwidth[u,v] != zero_bandwidth","P":"all simple directed A-to-E paths using F and containing C"},"params":["bw_A_B","bw_A_C","bw_A_E","bw_B_A","bw_B_C","bw_B_D","bw_B_E","bw_C_A","bw_C_D","bw_C_E","bw_D_A","bw_D_B","bw_D_C","bw_D_E","bw_E_B","bw_E_D","zero_bandwidth"],"derived":{"capacity[p]":"minimum bandwidth of the arcs in path p"},"decision_variables":{"selected[p]":"Binary, for each p in P"},"constraints":["sum(selected[p] for p in P) = 1"],"objective":"maximize sum(capacity[p] * selected[p] for p in P)"}

from itertools import permutations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bandwidth = {
        ("A", "B"): params["bw_A_B"],
        ("A", "C"): params["bw_A_C"],
        ("A", "E"): params["bw_A_E"],
        ("B", "A"): params["bw_B_A"],
        ("B", "C"): params["bw_B_C"],
        ("B", "D"): params["bw_B_D"],
        ("B", "E"): params["bw_B_E"],
        ("C", "A"): params["bw_C_A"],
        ("C", "D"): params["bw_C_D"],
        ("C", "E"): params["bw_C_E"],
        ("D", "A"): params["bw_D_A"],
        ("D", "B"): params["bw_D_B"],
        ("D", "C"): params["bw_D_C"],
        ("D", "E"): params["bw_D_E"],
        ("E", "B"): params["bw_E_B"],
        ("E", "D"): params["bw_E_D"],
    }
    zero_bandwidth = params["zero_bandwidth"]

    available_arcs = {
        arc
        for arc, capacity in bandwidth.items()
        if capacity != zero_bandwidth
    }

    # Distinct intermediate nodes guarantee that each candidate has no loops.
    intermediate_nodes = ("B", "C", "D")
    paths = []
    path_capacities = {}

    for count in range(1, len(intermediate_nodes) + 1):
        for intermediate_sequence in permutations(intermediate_nodes, count):
            if "C" not in intermediate_sequence:
                continue

            path = ("A",) + intermediate_sequence + ("E",)
            arcs = tuple(zip(path[:-1], path[1:]))

            if all(arc in available_arcs for arc in arcs):
                path_id = len(paths)
                paths.append(path)
                path_capacities[path_id] = min(
                    bandwidth[arc] for arc in arcs
                )

    model = pyo.ConcreteModel()
    model.path_ids = pyo.Set(
        initialize=range(len(paths)),
        ordered=True,
    )
    model.capacity = pyo.Param(
        model.path_ids,
        initialize=path_capacities,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(
        model.path_ids,
        domain=pyo.Binary,
    )

    # Tuple form also represents the infeasible empty-path case correctly.
    model.choose_path = pyo.Constraint(
        expr=(
            1,
            pyo.quicksum(
                model.selected[path_id] for path_id in model.path_ids
            ),
            1,
        )
    )
    model.total_bandwidth = pyo.Objective(
        expr=pyo.quicksum(
            model.capacity[path_id] * model.selected[path_id]
            for path_id in model.path_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_bandwidth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}