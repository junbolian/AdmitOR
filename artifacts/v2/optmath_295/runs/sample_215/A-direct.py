import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    nodes = list(range(5))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.pairs = pyo.Set(initialize=pairs, dimen=2)

    model.select = pyo.Var(model.nodes, domain=pyo.Binary)
    model.pair_flag = pyo.Var(model.pairs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            float(weights[i][j]) * m.pair_flag[i, j]
            for i, j in m.pairs
        )

    model.dispersion = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.facility_count = pyo.Constraint(
        expr=sum(model.select[i] for i in model.nodes) == num_facilities
    )

    def activation_a_rule(m, i, j):
        return m.pair_flag[i, j] <= m.select[i]

    def activation_b_rule(m, i, j):
        return m.pair_flag[i, j] <= m.select[j]

    def activation_c_rule(m, i, j):
        return m.pair_flag[i, j] >= m.select[i] + m.select[j] - 1

    model.act_a = pyo.Constraint(model.pairs, rule=activation_a_rule)
    model.act_b = pyo.Constraint(model.pairs, rule=activation_b_rule)
    model.act_c = pyo.Constraint(model.pairs, rule=activation_c_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.dispersion))
    return {"objective": obj_val, "status": "optimal"}