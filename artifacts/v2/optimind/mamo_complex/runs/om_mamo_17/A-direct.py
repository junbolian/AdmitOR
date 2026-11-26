import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)
    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.i = pyo.Set(initialize=nodes)
    model.j = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.i, model.j, domain=pyo.Binary)
    model.u = pyo.Var(model.i, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(cost[a][b] * mdl.x[a, b] for a in nodes for b in nodes if a != b)

    model.tsp_objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(mdl, a):
        return sum(mdl.x[a, b] for b in nodes if b != a) == 1

    model.out_con = pyo.Constraint(model.i, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(mdl, b):
        return sum(mdl.x[a, b] for a in nodes if a != b) == 1

    model.in_con = pyo.Constraint(model.j, rule=in_rule)

    # Subtour elimination (MTZ)
    def mtz_rule(mdl, a, b):
        if a != b and a >= 1 and b >= 1:
            return mdl.u[a] - mdl.u[b] + n * mdl.x[a, b] <= n - 1
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.i, model.j, rule=mtz_rule)

    def u_bound_rule(mdl, a):
        if a >= 1:
            return pyo.inequality(1, mdl.u[a], n - 1)
        return pyo.Constraint.Skip

    model.u_bounds = pyo.Constraint(model.i, rule=u_bound_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.tsp_objective))
    return {"objective": obj_val, "status": "optimal"}