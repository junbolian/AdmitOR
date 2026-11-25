import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    select_limit = params["select_limit"]
    dispersion = params["dispersion"]

    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    def disp(i, j):
        # support both dict-keyed and list-of-lists indexed dispersion params
        if isinstance(dispersion, dict):
            return dispersion[(i, j)]
        return dispersion[i][j]

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(disp(i, j) * model.y[(i, j)] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    model.selection_limit = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == select_limit
    )

    def activation_rule(m, i, j):
        return m.y[(i, j)] <= m.x[i]

    model.activation = pyo.Constraint(model.P, rule=activation_rule)

    def activation_rule2(m, i, j):
        return m.y[(i, j)] <= m.x[j]

    model.activation2 = pyo.Constraint(model.P, rule=activation_rule2)

    def activation_rule3(m, i, j):
        return m.y[(i, j)] >= m.x[i] + m.x[j] - 1

    model.activation3 = pyo.Constraint(model.P, rule=activation_rule3)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}