import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ["E", "F", "G", "H"]
    n = int(params["num_locations"])

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = float(params["cost_" + i + j])

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in nodes if i != j) == 1

    model.out_cons = pyo.Constraint(nodes, rule=out_rule)
    model.in_cons = pyo.Constraint(nodes, rule=in_rule)

    # Subtour elimination (DFJ) via Miller-Tucker-Zemlin-style ordering
    model.u = pyo.Var(nodes, bounds=(1, n))
    model.u[nodes[0]].fix(1)

    def mtz_rule(mdl, i, j):
        if i != nodes[0] and j != nodes[0] and i != j:
            return mdl.u[i] - mdl.u[j] + n * mdl.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(nodes, nodes, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}