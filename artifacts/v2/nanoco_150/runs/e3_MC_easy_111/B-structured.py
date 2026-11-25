# IR = {
#   "sets": {"V": [0,1,2,3,4,5,6,7,8,9], "A": [[0,1],[1,2],[1,7],[2,3],[2,6],[3,4],[3,8],[3,9],[4,5],[4,8],[5,6],[6,7],[7,8],[7,9],[8,9]]},
#   "params": {"capacity[i,j]": "nonnegative real from params['capacity_i_j'] for (i,j) in A", "maintenance[i,j]": "real from params['maintenance_i_j'] for (i,j) in A; unused", "coord_x[i]": "real from params['coord_x'][i] for i in V; unused", "coord_y[i]": "real from params['coord_y'][i] for i in V; unused"},
#   "variables": {"source_side[i]": "binary for i in V", "cut_arc[i,j]": "binary for (i,j) in A"},
#   "constraints": [
#     "source_side[0] = 1",
#     "source_side[9] = 0",
#     "cut_arc[i,j] >= source_side[i] - source_side[j] for (i,j) in A",
#     "cut_arc[i,j] <= source_side[i] for (i,j) in A",
#     "cut_arc[i,j] <= 1 - source_side[j] for (i,j) in A"
#   ],
#   "objective": "minimize sum(capacity[i,j] * cut_arc[i,j] for (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1),
        (1, 2),
        (1, 7),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 8),
        (5, 6),
        (6, 7),
        (7, 8),
        (7, 9),
        (8, 9),
    ]

    capacities = {
        (0, 1): params["capacity_0_1"],
        (1, 2): params["capacity_1_2"],
        (1, 7): params["capacity_1_7"],
        (2, 3): params["capacity_2_3"],
        (2, 6): params["capacity_2_6"],
        (3, 4): params["capacity_3_4"],
        (3, 8): params["capacity_3_8"],
        (3, 9): params["capacity_3_9"],
        (4, 5): params["capacity_4_5"],
        (4, 8): params["capacity_4_8"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (7, 8): params["capacity_7_8"],
        (7, 9): params["capacity_7_9"],
        (8, 9): params["capacity_8_9"],
    }

    maintenance = {
        (0, 1): params["maintenance_0_1"],
        (1, 2): params["maintenance_1_2"],
        (1, 7): params["maintenance_1_7"],
        (2, 3): params["maintenance_2_3"],
        (2, 6): params["maintenance_2_6"],
        (3, 4): params["maintenance_3_4"],
        (3, 8): params["maintenance_3_8"],
        (3, 9): params["maintenance_3_9"],
        (4, 5): params["maintenance_4_5"],
        (4, 8): params["maintenance_4_8"],
        (5, 6): params["maintenance_5_6"],
        (6, 7): params["maintenance_6_7"],
        (7, 8): params["maintenance_7_8"],
        (7, 9): params["maintenance_7_9"],
        (8, 9): params["maintenance_8_9"],
    }

    coord_x = params["coord_x"]
    coord_y = params["coord_y"]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 9)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.A, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.maintenance = pyo.Param(
        model.A, initialize=maintenance, within=pyo.Reals
    )
    model.coord_x = pyo.Param(
        model.V,
        initialize={node: coord_x[node] for node in range(10)},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.V,
        initialize={node: coord_y[node] for node in range(10)},
        within=pyo.Reals,
    )

    model.source_side = pyo.Var(model.V, domain=pyo.Binary)
    model.cut_arc = pyo.Var(model.A, domain=pyo.Binary)

    model.source_membership = pyo.Constraint(
        expr=model.source_side[0] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.source_side[9] == 0
    )

    def crossing_lower_rule(network, tail, head):
        return (
            network.cut_arc[tail, head]
            >= network.source_side[tail] - network.source_side[head]
        )

    def crossing_tail_rule(network, tail, head):
        return network.cut_arc[tail, head] <= network.source_side[tail]

    def crossing_head_rule(network, tail, head):
        return network.cut_arc[tail, head] <= 1 - network.source_side[head]

    model.crossing_lower = pyo.Constraint(
        model.A, rule=crossing_lower_rule
    )
    model.crossing_tail = pyo.Constraint(
        model.A, rule=crossing_tail_rule
    )
    model.crossing_head = pyo.Constraint(
        model.A, rule=crossing_head_rule
    )

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.capacity[tail, head] * model.cut_arc[tail, head]
            for tail, head in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}