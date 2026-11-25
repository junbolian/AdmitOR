# IR: {
#   "sets": {"N": [0,1,2,3,4,5], "A": "{(i,j) in N x N: i != j}"},
#   "params": {"supply_node0": "params['supply_node0']", "demand_node5": "params['demand_node5']", "cost[i,j]": "params[f'cost_{i}_{j}'] for (i,j) in A"},
#   "variables": {"x[i,j]": "Binary for (i,j) in A"},
#   "constraints": [
#     "sum_j x[0,j] - sum_i x[i,0] = supply_node0",
#     "sum_j x[k,j] - sum_i x[i,k] = 0 for k in {1,2,3,4}",
#     "sum_i x[i,5] - sum_j x[5,j] = demand_node5"
#   ],
#   "objective": "minimize sum_{(i,j) in A} cost[i,j] * x[i,j]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Demand is positive net inflow; the problem's final '-1' is a sign typo.
    nodes = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(initialize=params["supply_node0"])
    model.demand = pyo.Param(initialize=params["demand_node5"])
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in arcs
        },
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(network, node):
        outflow = sum(
            network.route_used[node, destination]
            for destination in network.nodes
            if destination != node
        )
        inflow = sum(
            network.route_used[origin, node]
            for origin in network.nodes
            if origin != node
        )
        if node == 0:
            return outflow - inflow == network.supply
        if node == 5:
            return inflow - outflow == network.demand
        return outflow - inflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination]
            * model.route_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}