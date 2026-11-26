import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = ["A", "B", "C", "D", "E"]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params["cost_" + i + j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def rule_obj(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=rule_obj, sense=pyo.minimize)

    def rule_out(m, i):
        return sum(m.x[(i, j)] for j in nodes if j != i) == 1

    model.out_degree = pyo.Constraint(nodes, rule=rule_out)

    def rule_in(m, j):
        return sum(m.x[(i, j)] for i in nodes if i != j) == 1

    model.in_degree = pyo.Constraint(nodes, rule=rule_in)

    # Subtour elimination (MTZ) for depot A
    model.u = pyo.Var(nodes, bounds=(1, len(nodes) - 1))
    model.u["A"].fix(1)

    def rule_mtz(m, i, j):
        if i != "A" and j != "A" and i != j:
            return m.u[i] - m.u[j] + (len(nodes) - 1) * m.x[(i, j)] <= len(nodes) - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint([(i, j) for (i, j) in arcs if i != "A" and j != "A"], rule=rule_mtz)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}