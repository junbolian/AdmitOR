# IR = {
#   "sets": {"N": "0..num_nodes-1", "T": "1..num_turbines", "A": "(i,j) in N x T with i != j"},
#   "params": {"cost_matrix": "input matrix; use upper triangle", "max_turbines_per_feeder": "K", "num_nodes": "n", "num_turbines": "t; n=t+1"},
#   "variables": {"x[i,j]": "binary; select directed parent-to-child cable", "f[i,j]": "nonnegative continuous; number of downstream turbines served"},
#   "constraints": [
#     "Each turbine has one parent: sum(i:(i,j) in A) x[i,j] = 1 for j in T.",
#     "Each turbine consumes one flow unit: sum(i:(i,j) in A) f[i,j] - sum(k:(j,k) in A) f[j,k] = 1 for j in T.",
#     "The substation supplies all turbines: sum(j in T) f[0,j] = t.",
#     "Flow requires a selected cable and respects feeder capacity: f[i,j] <= K*x[i,j] for (i,j) in A."
#   ],
#   "objective": "Minimize sum((i,j) in A) cost_matrix[min(i,j)][max(i,j)]*x[i,j]."
# }

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    node_count_input = params["num_nodes"]
    turbine_count_input = params["num_turbines"]
    feeder_capacity = params["max_turbines_per_feeder"]

    node_count = int(node_count_input)
    turbine_count = int(turbine_count_input)

    if (
        node_count != node_count_input
        or turbine_count != turbine_count_input
        or turbine_count < 1
        or node_count != turbine_count + 1
    ):
        return {"objective": None, "status": "invalid_node_counts"}

    if not math.isfinite(feeder_capacity) or feeder_capacity < 0:
        return {"objective": None, "status": "invalid_capacity"}

    if len(cost_matrix) != node_count or any(
        len(row) != node_count for row in cost_matrix
    ):
        return {"objective": None, "status": "invalid_cost_matrix"}

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(node_count), ordered=True)
    model.T = pyo.Set(initialize=range(1, turbine_count + 1), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(node_count)
            for j in range(1, turbine_count + 1)
            if i != j
        ],
        ordered=True,
    )

    model.feeder_capacity = pyo.Param(
        initialize=feeder_capacity, within=pyo.NonNegativeReals
    )
    model.turbine_total = pyo.Param(
        initialize=turbine_count, within=pyo.PositiveIntegers
    )
    model.cable_cost = pyo.Param(
        model.A,
        initialize=lambda mdl, i, j: cost_matrix[min(i, j)][max(i, j)],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def parent_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.N if i != j) == 1

    model.one_parent = pyo.Constraint(model.T, rule=parent_rule)

    def turbine_flow_rule(mdl, j):
        incoming = sum(mdl.f[i, j] for i in mdl.N if i != j)
        outgoing = sum(mdl.f[j, k] for k in mdl.T if k != j)
        return incoming - outgoing == 1

    model.turbine_flow_balance = pyo.Constraint(
        model.T, rule=turbine_flow_rule
    )

    model.substation_supply = pyo.Constraint(
        expr=sum(model.f[0, j] for j in model.T) == model.turbine_total
    )

    def cable_capacity_rule(mdl, i, j):
        return mdl.f[i, j] <= mdl.feeder_capacity * mdl.x[i, j]

    model.cable_capacity = pyo.Constraint(model.A, rule=cable_capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cable_cost[i, j] * model.x[i, j] for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}