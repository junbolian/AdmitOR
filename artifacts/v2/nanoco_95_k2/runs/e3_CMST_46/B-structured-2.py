# {
#   "sets": {"V": "0..15", "H": "1..15", "E": "{(i,j): i,j in V, i<j}", "A": "{(i,j): i in V, j in H, i!=j}"},
#   "params": {"C": "params['splitter_port_limit']", "c[i,j]": "params[f'dist_{i}_{j}'] for (i,j) in E"},
#   "variables": {"x[i,j]": "Binary for (i,j) in A; selected parent-to-child arc", "f[i,j]": "NonNegativeReals for (i,j) in A; number of homes served downstream"},
#   "constraints": [
#     "For each j in H: sum(x[i,j] for i in V if i!=j) = 1",
#     "For each j in H: sum(f[i,j] for i in V if i!=j) - sum(f[j,k] for k in H if k!=j) = 1",
#     "sum(f[0,j] for j in H) = |H|",
#     "For each (i,j) in A: f[i,j] >= x[i,j]",
#     "For each (i,j) in A: f[i,j] <= C*x[i,j]"
#   ],
#   "objective": "Minimize sum(c[min(i,j),max(i,j)]*x[i,j] for (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(16))
    homes = tuple(range(1, 16))
    edges = tuple(
        (i, j) for i in vertices for j in vertices if i < j
    )
    arcs = tuple(
        (i, j) for i in vertices for j in homes if i != j
    )

    capacity = params["splitter_port_limit"]
    costs = {
        (i, j): params[f"dist_{i}_{j}"]
        for i, j in edges
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vertices, ordered=True)
    model.H = pyo.Set(initialize=homes, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.C = pyo.Param(initialize=capacity, within=pyo.Reals)
    model.c = pyo.Param(model.E, initialize=costs, within=pyo.Reals)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def one_parent_rule(network, j):
        return sum(
            network.x[i, j] for i in network.V if i != j
        ) == 1

    model.one_parent = pyo.Constraint(model.H, rule=one_parent_rule)

    def flow_balance_rule(network, j):
        incoming = sum(
            network.f[i, j] for i in network.V if i != j
        )
        outgoing = sum(
            network.f[j, k] for k in network.H if k != j
        )
        return incoming - outgoing == 1

    model.flow_balance = pyo.Constraint(
        model.H, rule=flow_balance_rule
    )

    model.root_supply = pyo.Constraint(
        expr=sum(model.f[0, j] for j in model.H) == len(homes)
    )

    def selected_flow_rule(network, i, j):
        return network.f[i, j] >= network.x[i, j]

    model.selected_flow = pyo.Constraint(
        model.A, rule=selected_flow_rule
    )

    def branch_capacity_rule(network, i, j):
        return network.f[i, j] <= network.C * network.x[i, j]

    model.branch_capacity = pyo.Constraint(
        model.A, rule=branch_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.c[min(i, j), max(i, j)] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    # Positive consumption at every home excludes disconnected cycles.
    # Thus the parent arcs form a rooted tree, and feeder flow equals
    # the number of homes in its subtree. Bounding every arc by C is
    # valid because every downstream subtree lies within a feeder subtree.
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}