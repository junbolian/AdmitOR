# IR: {"sets":{"N":[0,1,2,3,4],"A":"(i,j) in N x N with i != j","P":"(i,j) in A with i < j"},"params":{"distances":"Directed distances d[i,j], read from params['distances']; each unordered pair uses its i<j directed value"},"variables":{"selected[i]":"binary for i in N","paired[i,j]":"binary for (i,j) in P"},"constraints":["sum(selected[i] for i in N) == 3","paired[i,j] <= selected[i] for (i,j) in P","paired[i,j] <= selected[j] for (i,j) in P","paired[i,j] >= selected[i] + selected[j] - 1 for (i,j) in P"],"objective":"maximize sum(d[i,j] * paired[i,j] for (i,j) in P)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(5)
    directed_pairs = [
        (i, j) for i in nodes for j in nodes if i != j
    ]
    unordered_pairs = [
        (i, j) for i in nodes for j in nodes if i < j
    ]
    raw_distances = params["distances"]

    def read_distance(i, j):
        """Accept pair-keyed mappings, nested mappings/matrices, or 20 values."""
        if isinstance(raw_distances, Mapping):
            possible_keys = (
                (i, j),
                f"{i},{j}",
                f"{i}, {j}",
                f"({i},{j})",
                f"({i}, {j})",
                f"{i}_{j}",
            )
            for pair_key in possible_keys:
                if pair_key in raw_distances:
                    return float(raw_distances[pair_key])

            row_key = i if i in raw_distances else str(i)
            row = raw_distances[row_key]
            if isinstance(row, Mapping):
                column_key = j if j in row else str(j)
                return float(row[column_key])
            return float(row[j])

        if len(raw_distances) == len(directed_pairs):
            position = directed_pairs.index((i, j))
            return float(raw_distances[position])

        return float(raw_distances[i][j])

    distance_values = {
        (i, j): read_distance(i, j) for i, j in directed_pairs
    }

    model = pyo.ConcreteModel()
    model.facilities = pyo.Set(initialize=nodes, ordered=True)
    model.directed_pairs = pyo.Set(
        dimen=2, initialize=directed_pairs, ordered=True
    )
    model.facility_pairs = pyo.Set(
        dimen=2, initialize=unordered_pairs, ordered=True
    )
    model.distance_data = pyo.Param(
        model.directed_pairs,
        initialize=distance_values,
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.facilities, domain=pyo.Binary)
    model.paired = pyo.Var(model.facility_pairs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=sum(model.selected[i] for i in model.facilities) == 3
    )

    def first_endpoint_rule(problem, i, j):
        return problem.paired[i, j] <= problem.selected[i]

    def second_endpoint_rule(problem, i, j):
        return problem.paired[i, j] <= problem.selected[j]

    def both_endpoints_rule(problem, i, j):
        return (
            problem.paired[i, j]
            >= problem.selected[i] + problem.selected[j] - 1
        )

    model.first_endpoint_limit = pyo.Constraint(
        model.facility_pairs, rule=first_endpoint_rule
    )
    model.second_endpoint_limit = pyo.Constraint(
        model.facility_pairs, rule=second_endpoint_rule
    )
    model.both_endpoints_link = pyo.Constraint(
        model.facility_pairs, rule=both_endpoints_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=sum(
            model.distance_data[i, j] * model.paired[i, j]
            for i, j in model.facility_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises when it cannot load a feasible solution.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    # Success depends solely on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}