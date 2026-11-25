import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural sizes
    num_producers = 3
    num_contracts = 4
    producers = range(num_producers)
    contracts = range(num_contracts)

    # Read numeric quantities from params
    capacity = params["capacity"]        # per producer
    demand = params["demand"]            # per contract
    min_delivery = params["min_delivery"]  # per producer
    cost = params["cost"]                # [producer][contract]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_producers - 1)
    model.C = pyo.RangeSet(0, num_contracts - 1)

    # Continuous delivery amount
    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    # Binary contribution indicator
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    # Objective: minimize total cost
    def obj_rule(m):
        return sum(
            cost[i][j] * m.x[i, j]
            for i in producers
            for j in contracts
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Capacity constraints per producer
    def cap_rule(m, i):
        return sum(m.x[i, j] for j in contracts) <= capacity[i]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    # Demand satisfaction per contract
    def dem_rule(m, j):
        return sum(m.x[i, j] for i in producers) >= demand[j]
    model.dem_con = pyo.Constraint(model.C, rule=dem_rule)

    # At least two producers per contract
    def two_rule(m, j):
        return sum(m.y[i, j] for i in producers) >= 2
    model.two_con = pyo.Constraint(model.C, rule=two_rule)

    # Big-M linking: x <= capacity[i] * y, and min delivery when contributing
    bigM = {}
    for i in producers:
        bigM[i] = capacity[i]

    def link_upper_rule(m, i, j):
        return m.x[i, j] <= bigM[i] * m.y[i, j]
    model.link_upper = pyo.Constraint(model.P, model.C, rule=link_upper_rule)

    def link_lower_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.link_lower = pyo.Constraint(model.P, model.C, rule=link_lower_rule)

    # Solve with HiGHS
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}