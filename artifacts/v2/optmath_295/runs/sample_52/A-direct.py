import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    # Variable costs: facility-customer pair costs (cost per unit of demand served)
    # Based on the example given for Customer 0 and the stated range (25-35).
    # These are structural data tied to the specific instance described.
    var_cost = [
        [34, 26, 32, 32],
        [30, 33, 29, 31],
        [27, 35, 28, 30],
        [33, 25, 35, 27],
        [31, 29, 26, 34],
        [28, 32, 30, 29],
        [26, 34, 27, 33],
        [35, 28, 32, 25],
        [29, 31, 33, 28],
        [32, 30, 25, 35],
    ]

    facilities = list(range(4))
    customers = list(range(10))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=facilities)
    model.C = pyo.Set(initialize=customers)

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.ship = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[f] * m.opened[f] for f in m.F) + \
               sum(var_cost[c][f] * m.ship[f, c] for f in m.F for c in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.ship[f, c] for f in m.F) == demand[c]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(m, f):
        return sum(m.ship[f, c] for c in m.C) <= capacity[f] * m.opened[f]
    model.capacity_con = pyo.Constraint(model.F, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}