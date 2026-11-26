# IR: {"sets":{"N":"0..8","I":"1..7","A":"N x N"},"params":{"capacity":"nonnegative directed capacities from params['capacity']; 9x9 nested matrix or flat row-major array"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for j in N) == sum(flow[j,i] for j in N) for i in I"],"objective":"maximize sum(flow[0,j] - flow[j,0] for j in N)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_input = params["capacity"]
    node_count = 9

    if len(capacity_input) == node_count * node_count:
        capacities = {
            (i, j): capacity_input[i * node_count + j]
            for i in range(node_count)
            for j in range(node_count)
        }
    elif (
        len(capacity_input) == node_count
        and all(len(row) == node_count for row in capacity_input)
    ):
        capacities = {
            (i, j): capacity_input[i][j]
            for i in range(node_count)
            for j in range(node_count)
        }
    else:
        raise ValueError(
            "capacity must be a 9x9 matrix or a flat array of 81 entries."
        )

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, node_count - 1)
    model.I = pyo.RangeSet(1, node_count - 2)
    model.A = pyo.Set(
        dimen=2,
        initialize=((i, j) for i in model.N for j in model.N),
    )

    model.capacity = pyo.Param(
        model.A,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def capacity_rule(model, i, j):
        return model.flow[i, j] <= model.capacity[i, j]

    model.capacity_limits = pyo.Constraint(model.A, rule=capacity_rule)

    def conservation_rule(model, i):
        return (
            sum(model.flow[i, j] for j in model.N)
            == sum(model.flow[j, i] for j in model.N)
        )

    model.flow_conservation = pyo.Constraint(
        model.I, rule=conservation_rule
    )

    model.total_transfer = pyo.Objective(
        expr=sum(
            model.flow[0, j] - model.flow[j, 0]
            for j in model.N
        ),
        sense=pyo.maximize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_transfer))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}