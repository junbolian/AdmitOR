# {
#   "sets": {
#     "V": [0, 1, 2, 3, 4, 5, 6],
#     "I": [1, 2, 3, 4, 5],
#     "A": [[0,1],[0,2],[0,3],[0,5],[0,6],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[2,6],[3,0],[3,1],[3,2],[3,4],[3,5],[3,6],[4,0],[4,1],[4,2],[4,3],[4,5],[4,6],[5,0],[5,1],[5,2],[5,3],[5,4],[5,6],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5]]
#   },
#   "params": {
#     "capacity[i,j]": "params['capacity_' + str(i) + '_' + str(j)] for each (i,j) in A; nonnegative; thousands kg/day"
#   },
#   "decision_variables": {
#     "flow[i,j]": "nonnegative continuous for each (i,j) in A; thousands kg/day"
#   },
#   "constraints": [
#     "flow[i,j] <= capacity[i,j] for each (i,j) in A",
#     "sum(flow[i,j] for incoming arcs (i,j)) = sum(flow[j,k] for outgoing arcs (j,k)) for each j in I"
#   ],
#   "objective": "maximize sum(flow[0,j] for outgoing arcs (0,j)) - sum(flow[i,0] for incoming arcs (i,0)); thousands kg/day"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    )

    capacities = {
        (0, 1): params["capacity_0_1"],
        (0, 2): params["capacity_0_2"],
        (0, 3): params["capacity_0_3"],
        (0, 5): params["capacity_0_5"],
        (0, 6): params["capacity_0_6"],
        (1, 0): params["capacity_1_0"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (1, 5): params["capacity_1_5"],
        (2, 0): params["capacity_2_0"],
        (2, 1): params["capacity_2_1"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (2, 6): params["capacity_2_6"],
        (3, 0): params["capacity_3_0"],
        (3, 1): params["capacity_3_1"],
        (3, 2): params["capacity_3_2"],
        (3, 4): params["capacity_3_4"],
        (3, 5): params["capacity_3_5"],
        (3, 6): params["capacity_3_6"],
        (4, 0): params["capacity_4_0"],
        (4, 1): params["capacity_4_1"],
        (4, 2): params["capacity_4_2"],
        (4, 3): params["capacity_4_3"],
        (4, 5): params["capacity_4_5"],
        (4, 6): params["capacity_4_6"],
        (5, 0): params["capacity_5_0"],
        (5, 1): params["capacity_5_1"],
        (5, 2): params["capacity_5_2"],
        (5, 3): params["capacity_5_3"],
        (5, 4): params["capacity_5_4"],
        (5, 6): params["capacity_5_6"],
        (6, 0): params["capacity_6_0"],
        (6, 1): params["capacity_6_1"],
        (6, 2): params["capacity_6_2"],
        (6, 3): params["capacity_6_3"],
        (6, 4): params["capacity_6_4"],
        (6, 5): params["capacity_6_5"],
    }

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, 6)
    model.I = pyo.RangeSet(1, 5)
    model.A = pyo.Set(dimen=2, initialize=arcs)
    model.capacity = pyo.Param(
        model.A,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.A, rule=capacity_rule)

    def conservation_rule(network, city):
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == city
        )
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == city
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.I,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(
                model.flow[origin, destination]
                for origin, destination in arcs
                if origin == 0
            )
            - sum(
                model.flow[origin, destination]
                for origin, destination in arcs
                if destination == 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}