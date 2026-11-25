import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---- Structural constants ----
    P = list(range(5))  # producers
    C = list(range(5))  # contracts

    # ---- Parameters from params ----
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    model = pyo.ConcreteModel("energy_allocation")

    model.P = pyo.Set(initialize=P)
    model.C = pyo.Set(initialize=C)
    model.PC = pyo.Set(initialize=[(p, c) for p in P for c in C], dimen=2)

    # Decision variable: energy delivered by producer p to contract c
    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)

    # Binary indicator: does producer p contribute to contract c?
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    # Objective: minimize total production cost
    model.total_cost = pyo.Objective(
        expr=sum(cost[p][c] * model.x[p, c] for p in P for c in C),
        sense=pyo.minimize,
    )

    # Capacity: producer total delivery cannot exceed its capacity
    def capacity_rule(m, p):
        return sum(m.x[p, c] for c in C) <= capacity[p]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    # Demand: each contract's demand must be fully met
    def demand_rule(m, c):
        return sum(m.x[p, c] for p in P) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    # Minimum contributors: each contract needs enough contributing producers
    def contributors_rule(m, c):
        return sum(m.y[p, c] for p in P) >= min_contributors[c]

    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    # Linking: delivery bounded by indicator and minimum delivery
    def link_lower_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]

    def link_upper_rule(m, p, c):
        # Big-M upper bound only if contributing
        big_m = min(capacity[p], demand[c])
        return m.x[p, c] <= big_m * m.y[p, c]

    model.link_lower_con = pyo.Constraint(model.PC, rule=link_lower_rule)
    model.link_upper_con = pyo.Constraint(model.PC, rule=link_upper_rule)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}