import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["truck_capacity"]
    weights = list(params["good_weights"])

    num_goods = len(weights)
    num_trucks = num_goods

    goods = list(range(num_goods))
    trucks = list(range(num_trucks))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(goods, trucks, domain=pyo.Binary)
    model.y = pyo.Var(trucks, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[t] for t in trucks)

    model.total_trucks = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, g):
        return sum(m.x[g, t] for t in trucks) == 1

    model.assign_con = pyo.Constraint(goods, rule=assign_rule)

    def cap_rule(m, t):
        return sum(weights[g] * m.x[g, t] for g in goods) <= capacity * m.y[t]

    model.cap_con = pyo.Constraint(trucks, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_trucks))
    return {"objective": obj_val, "status": "optimal"}