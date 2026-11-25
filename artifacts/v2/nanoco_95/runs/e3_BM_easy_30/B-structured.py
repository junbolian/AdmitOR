# IR: {"sets":{"cells":"0..8","links":[[0,1],[0,2],[0,3],[0,5],[0,7],[1,5],[1,7],[2,3],[2,6],[2,7],[2,8],[3,7],[4,5],[4,6],[5,7],[5,8]]},"params":{"link_weights":"value of each link in listed order","cell_capacities":"capacity indexed by cell"},"variables":{"selected[i,j]":"binary for each available link"},"constraints":["For each cell c: sum(selected[i,j] for available links incident to c) <= cell_capacities[c]."],"objective":"Maximize sum(link_weights[k] * selected[i,j] for k,(i,j) in enumerated links)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    links = (
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 5),
        (0, 7),
        (1, 5),
        (1, 7),
        (2, 3),
        (2, 6),
        (2, 7),
        (2, 8),
        (3, 7),
        (4, 5),
        (4, 6),
        (5, 7),
        (5, 8),
    )
    link_weights = params["link_weights"]
    cell_capacities = params["cell_capacities"]

    model = pyo.ConcreteModel()
    model.cells = pyo.RangeSet(0, 8)
    model.links = pyo.Set(dimen=2, initialize=links, ordered=True)

    model.link_value = pyo.Param(
        model.links,
        initialize={
            (i, j): link_weights[k]
            for k, (i, j) in enumerate(links)
        },
        within=pyo.Reals,
    )
    model.cell_capacity = pyo.Param(
        model.cells,
        initialize={cell: cell_capacities[cell] for cell in range(9)},
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.links, domain=pyo.Binary)

    def capacity_rule(instance, cell):
        return (
            sum(
                instance.selected[i, j]
                for i, j in links
                if i == cell or j == cell
            )
            <= instance.cell_capacity[cell]
        )

    model.capacity_limits = pyo.Constraint(
        model.cells, rule=capacity_rule
    )
    model.total_value = pyo.Objective(
        expr=sum(
            model.link_value[i, j] * model.selected[i, j]
            for i, j in links
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}