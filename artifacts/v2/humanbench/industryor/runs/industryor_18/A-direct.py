import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    devices = ["A", "B", "C", "D"]

    setup_cost = params["setup_cost"]
    production_cost = params["production_cost"]
    capacity = params["capacity"]
    demand = params["demand"]

    # Map device name -> value, handling both dict and list inputs
    def get_val(source, d):
        if isinstance(source, dict):
            return source[d]
        return source[devices.index(d)]

    model = pyo.ConcreteModel()

    model.DEV = pyo.Set(initialize=devices)

    model.x = pyo.Var(model.DEV, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.DEV, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            get_val(setup_cost, d) * m.y[d]
            + get_val(production_cost, d) * m.x[d]
            for d in m.DEV
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m):
        return sum(m.x[d] for d in m.DEV) == demand

    model.demand_con = pyo.Constraint(rule=demand_rule)

    def cap_rule(m, d):
        return m.x[d] <= get_val(capacity, d) * m.y[d]

    model.cap_con = pyo.Constraint(model.DEV, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}