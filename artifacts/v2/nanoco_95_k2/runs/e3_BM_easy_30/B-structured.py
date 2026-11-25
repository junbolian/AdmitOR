# IR: {"sets":{"cells":[0,1,2,3,4,5,6,7,8],"edges":[[0,1],[0,2],[0,3],[0,5],[0,7],[1,5],[1,7],[2,3],[2,6],[2,7],[2,8],[3,7],[4,5],[4,6],[5,7],[5,8]]},"params":{"edge_weights":"params['edge_weights'][k], indexed by stated edge order","cell_capacities":"params['cell_capacities'][cell], indexed by cell"},"decision_variables":{"selected[k]":"binary for each edge index k"},"constraints":["For each cell: sum(selected[k] for edges incident to cell) <= cell_capacities[cell]."],"objective":"Maximize sum(edge_weights[k] * selected[k] for all edge indices k)."}

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
    model.edge_ids = pyo.RangeSet(0, len(edges) - 1)

    model.task_weights = pyo.Param(
        model.edge_ids,
        initialize=lambda _, edge_id: edge_weights[edge_id],
        within=pyo.Reals,
    )
    model.capacity_limits = pyo.Param(
        model.cells,
        initialize=lambda _, cell: cell_capacities[cell],
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.edge_ids, domain=pyo.Binary)

    incident_edges = {
        cell: tuple(
            edge_id
            for edge_id, endpoints in enumerate(edges)
            if cell in endpoints
        )
        for cell in model.cells
    }

    def capacity_rule(instance, cell):
        return (
            sum(instance.selected[edge_id] for edge_id in incident_edges[cell])
            <= instance.capacity_limits[cell]
        )

    model.cell_capacity_constraints = pyo.Constraint(
        model.cells, rule=capacity_rule
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.task_weights[edge_id] * model.selected[edge_id]
            for edge_id in model.edge_ids
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}