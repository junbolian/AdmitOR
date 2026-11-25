import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_capacity = params["truck_capacity"]
    shipment_weights = params["shipment_weights"]
    num_trucks = params["num_trucks"]

    shipments = list(range(len(shipment_weights)))
    trucks = list(range(num_trucks))

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=shipments)
    model.T = pyo.Set(initialize=trucks)

    model.x = pyo.Var(model.S, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[t] for t in m.T)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, s):
        return sum(m.x[s, t] for t in m.T) == 1

    model.assign_con = pyo.Constraint(model.S, rule=assign_rule)

    def cap_rule(m, t):
        return sum(shipment_weights[s] * m.x[s, t] for s in m.S) <= truck_capacity * m.y[t]

    model.cap_con = pyo.Constraint(model.T, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}