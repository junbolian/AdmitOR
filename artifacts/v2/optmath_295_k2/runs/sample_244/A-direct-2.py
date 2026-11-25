import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = [f"facility_{i}" for i in range(4)]
    customers = [f"customer_{j}" for j in range(6)]

    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=facilities)
    model.CUS = pyo.Set(initialize=customers)
    model.LINKS = pyo.Set(initialize=[(f, c) for f in facilities for c in customers])

    model.open_fac = pyo.Var(model.FAC, domain=pyo.Binary)
    model.ship = pyo.Var(model.LINKS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.open_fac[f] for i, f in enumerate(facilities)) + \
               sum(shipping_cost[i][j] * m.ship[f, c]
                   for i, f in enumerate(facilities)
                   for j, c in enumerate(customers))

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.ship[f, c] for f in m.FAC) >= demand[customers.index(c)]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def capacity_rule(m, f):
        return sum(m.ship[f, c] for c in m.CUS) <= capacity[facilities.index(f)] * m.open_fac[f]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}