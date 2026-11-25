import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    cost = params["transition_cost_matrix"]
    nodes = list(range(n))

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.N, model.N, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.N for j in m.N if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each node has exactly one outgoing arc
    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.N if j != i) == 1

    model.out_arc = pyo.Constraint(model.N, rule=out_rule)

    # Each node has exactly one incoming arc
    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.N if i != j) == 1

    model.in_arc = pyo.Constraint(model.N, rule=in_rule)

    # Subtour elimination via MTZ
    model.u = pyo.Var(model.N, domain=pyo.NonNegativeReals, bounds=(0, n - 1))
    model.u[0].fix(0)

    # For non-depot nodes, u in [1, n-1]
    def mtz_bound_rule(m, i):
        if i == 0:
            return pyo.Constraint.Skip
        return (1, m.u[i], n - 1)

    model.u_bounds = pyo.Constraint(model.N, rule=mtz_bound_rule)

    def mtz_rule(m, i, j):
        if i == 0 or j == 0 or i == j:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + (n - 1) * m.x[i, j] <= n - 2

    model.mtz = pyo.Constraint(model.N, model.N, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}