import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = [0, 1, 2, 3]
    pairs = [(i, j) for i in locations for j in locations if i != j]
    weights = {
        (0, 1): params["weights_01"],
        (0, 2): params["weights_02"],
        (0, 3): params["weights_03"],
        (1, 0): params["weights_10"],
        (1, 2): params["weights_12"],
        (1, 3): params["weights_13"],
        (2, 0): params["weights_20"],
        (2, 1): params["weights_21"],
        (2, 3): params["weights_23"],
        (3, 0): params["weights_30"],
        (3, 1): params["weights_31"],
        (3, 2): params["weights_32"],
    }
    num_select = params["facilities_to_select"]

    model = pyo.ConcreteModel()
    model.L = pyo.Set(initialize=locations)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.L, domain=pyo.Binary)
    model.z = pyo.Var(model.P, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(weights[i, j] * model.z[i, j] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    def select_count_rule(m):
        return sum(m.x[i] for i in m.L) == num_select

    model.select_count = pyo.Constraint(rule=select_count_rule)

    def pair_ub_rule(m, i, j):
        return m.z[i, j] <= m.x[i]

    def pair_ub2_rule(m, i, j):
        return m.z[i, j] <= m.x[j]

    def pair_lb_rule(m, i, j):
        return m.z[i, j] >= m.x[i] + m.x[j] - 1

    model.pair_ub = pyo.Constraint(model.P, rule=pair_ub_rule)
    model.pair_ub2 = pyo.Constraint(model.P, rule=pair_ub2_rule)
    model.pair_lb = pyo.Constraint(model.P, rule=pair_lb_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}