# IR: {"sets":{"cells":[0,1,2,3,4,5,6,7,8],"edges":[[0,1],[0,2],[0,3],[0,5],[0,7],[1,5],[1,7],[2,3],[2,6],[2,7],[2,8],[3,7],[4,5],[4,6],[5,7],[5,8]],"edge_indices":"0..15"},"params":{"edge_weights":"params['edge_weights'][k] for each edge index k","cell_capacities":"params['cell_capacities'][c] for each cell c"},"decision_variables":{"selected[k]":"binary for each edge index k"},"constraints":["For each cell c: sum(selected[k] for edges k incident to c) <= cell_capacities[c]."],"objective":"Maximize sum(edge_weights[k] * selected[k] for all edge indices k)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
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
    edge_weights = params["edge_weights"]
    cell_capacities = params["cell_capacities"]

    model = pyo.ConcreteModel()
    model.cells = pyo.RangeSet(0, 8)
    model.edge_indices = pyo.RangeSet(0, 15)

    model.edge_weights = pyo.Param(
        model.edge_indices,
        initialize={k: edge_weights[k] for k in range(len(edges))},
        within=pyo.Reals,
    )
    model.cell_capacities = pyo.Param(
        model.cells,
        initialize={c: cell_capacities[c] for c in range(9)},
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.edge_indices, domain=pyo.Binary)

    incident_edges = {
        c: tuple(k for k, endpoints in enumerate(edges) if c in endpoints)
        for c in range(9)
    }

    def capacity_rule(instance, c):
        return (
            sum(instance.selected[k] for k in incident_edges[c])
            <= instance.cell_capacities[c]
        )

    model.capacity_limits = pyo.Constraint(model.cells, rule=capacity_rule)
    model.total_value = pyo.Objective(
        expr=sum(
            model.edge_weights[k] * model.selected[k]
            for k in model.edge_indices
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this expected error when no solution can be loaded.
        # Re-raise unrelated runtime errors rather than hiding them.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}