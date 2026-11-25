import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = ["facility_0", "facility_1", "facility_2", "facility_3"]
    customers = ["customer_0", "customer_1", "customer_2", "customer_3",
                 "customer_4", "customer_5"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities)
    model.C = pyo.Set(initialize=customers)
    model.Link = pyo.Set(
        initialize=[(f, c) for f in facilities for c in customers], dimen=2
    )

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    def fixed_cost_get(f):
        return fixed_cost[facilities.index(f)] if isinstance(fixed_cost, (list, tuple)) else fixed_cost[f]

    def capacity_get(f):
        return capacity[facilities.index(f)] if isinstance(capacity, (list, tuple)) else capacity[f]

    def demand_get(c):
        return demand[customers.index(c)] if isinstance(demand, (list, tuple)) else demand[c]

    def ship_cost_get(f, c):
        row = shipping_cost[facilities.index(f)] if isinstance(shipping_cost, (list, tuple)) else shipping_cost[f]
        return row[customers.index(c)] if isinstance(row, (list, tuple)) else row[c]

    model.open = pyo.Var(model.F, domain=pyo.Binary)
    model.ship = pyo.Var(model.Link, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return (sum(fixed_cost_get(f) * m.open[f] for f in m.F)
                + sum(ship_cost_get(f, c) * m.ship[f, c] for (f, c) in m.Link))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.ship[f, c] for f in m.F) == demand_get(c)

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, f):
        return sum(m.ship[f, c] for c in m.C) <= capacity_get(f) * m.open[f]

    model.cap_con = pyo.Constraint(model.F, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}