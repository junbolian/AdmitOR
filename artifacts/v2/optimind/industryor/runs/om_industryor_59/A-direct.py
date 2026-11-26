import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    demand = params["demand"]
    devices = ["A", "B", "C", "D"]
    prep_cost = params["prep_cost"]
    unit_cost = params["unit_cost"]
    capacity = params["capacity"]

    # Allow dicts or lists keyed by device name or index
    def get(d, key, idx):
        if isinstance(d, dict):
            return d[key]
        return d[idx]

    model = pyo.ConcreteModel()

    model.DEV = pyo.Set(initialize=devices)

    # y[i] = 1 if device i is enabled
    model.y = pyo.Var(model.DEV, domain=pyo.Binary)
    # x[i] = units produced on device i
    model.x = pyo.Var(model.DEV, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            get(prep_cost, i, k) * m.y[i] + get(unit_cost, i, k) * m.x[i]
            for k, i in enumerate(m.DEV)
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand must be met exactly
    model.demand_con = pyo.Constraint(
        expr=sum(model.x[i] for i in model.DEV) == demand
    )

    # Capacity linking: x[i] <= capacity[i] * y[i]
    def cap_rule(m, i, k):
        return m.x[i] <= get(capacity, i, k) * m.y[i]
    model.cap_con = pyo.Constraint(model.DEV, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}