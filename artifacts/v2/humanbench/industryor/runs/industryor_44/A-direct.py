import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_customers"])
    dist = params["distance_matrix"]

    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.nodes, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    def obj_rule(mdl):
        return sum(dist[i][j] * mdl.x[i, j] for (i, j) in mdl.arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing and one incoming arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.out_con = pyo.Constraint(model.nodes, rule=out_rule)
    model.in_con = pyo.Constraint(model.nodes, rule=in_rule)

    # Fix depot (node 0 == location 1) as start
    model.u[0].fix(0)

    # Subtour elimination (MTZ)
    def mtz_rule(mdl, i, j):
        if i != 0 and j != 0 and i != j:
            return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}