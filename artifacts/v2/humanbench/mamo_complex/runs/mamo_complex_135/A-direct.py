import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [1, 2, 3, 4]

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params["c{}{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j])
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in nodes if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in nodes if i != j) == 1

    model.out_flow = pyo.Constraint(nodes, rule=out_rule)
    model.in_flow = pyo.Constraint(nodes, rule=in_rule)

    # Subtour elimination (MTZ) for the single tour
    n = len(nodes)
    order = list(range(n + 1))

    def u_bounds(m, i):
        return (1, n - 1)

    model.u = pyo.Var(order[1:], bounds=u_bounds)

    def mtz_rule(m, i, j):
        if i != j and i != 1 and j != 1 and i in order[1:] and j in order[1:]:
            return m.u[i] - m.u[j] + (n - 1) * m.x[(i, j)] <= n - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint([(i, j) for i in order[1:] for j in order[1:]], rule=mtz_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}