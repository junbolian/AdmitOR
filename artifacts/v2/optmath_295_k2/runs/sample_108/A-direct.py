import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants
    producers = [0, 1, 2]
    contracts = [0, 1, 2, 3]

    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    # Decision variable: energy produced by producer p for contract c
    model.x = pyo.Var(producers, contracts, domain=pyo.NonNegativeReals)

    # Binary: whether producer p participates in contract c
    model.y = pyo.Var(producers, contracts, domain=pyo.Binary)

    # Objective: minimize total production cost
    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in producers for c in contracts)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity constraint per producer
    def cap_rule(m, p):
        return sum(m.x[p, c] for c in contracts) <= capacity[p]
    model.cap = pyo.Constraint(producers, rule=cap_rule)

    # Demand constraint per contract
    def dem_rule(m, c):
        return sum(m.x[p, c] for p in producers) >= demand[c]
    model.dem = pyo.Constraint(contracts, rule=dem_rule)

    # At least two producers per contract
    def minsup_rule(m, c):
        return sum(m.y[p, c] for p in producers) >= 2
    model.minsup = pyo.Constraint(contracts, rule=minsup_rule)

    # Minimum delivery if participates; also links x and y
    def lb_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]
    model.lb = pyo.Constraint(producers, contracts, rule=lb_rule)

    # Upper bound on x when participating (capacity per contract link)
    def ub_rule(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]
    model.ub = pyo.Constraint(producers, contracts, rule=ub_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}