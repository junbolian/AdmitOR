import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    pair_weights = params["pair_weights"]
    facilities_to_select = params["facilities_to_select"]

    nodes = [0, 1, 2, 3]
    pairs = [(0, 1), (0, 2), (0, 3),
             (1, 0), (1, 2), (1, 3),
             (2, 0), (2, 1), (2, 3),
             (3, 0), (3, 1), (3, 2)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.z = pyo.Var(pairs, domain=pyo.Binary)

    def objective_rule(m):
        return sum(pair_weights[k] * m.z[pairs[k]] for k in range(len(pairs)))
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    model.count_con = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == facilities_to_select
    )

    def pair_rule(m, i, j):
        return m.z[(i, j)] <= m.x[i]

    def pair_rule2(m, i, j):
        return m.z[(i, j)] <= m.x[j]

    def pair_rule3(m, i, j):
        return m.z[(i, j)] >= m.x[i] + m.x[j] - 1

    model.pair_con1 = pyo.Constraint(pairs, rule=pair_rule)
    model.pair_con2 = pyo.Constraint(pairs, rule=pair_rule2)
    model.pair_con3 = pyo.Constraint(pairs, rule=pair_rule3)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}