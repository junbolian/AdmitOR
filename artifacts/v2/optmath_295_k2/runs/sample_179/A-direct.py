import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    cost_p0_c0 = params["cost_p0_c0"]
    cost_p0_c1 = params["cost_p0_c1"]

    P = len(producer_capacity)
    C = len(contract_demand)

    def cost_matrix():
        cm = {}
        for i in range(P):
            for j in range(C):
                if i == 0 and j == 0:
                    cm[(i, j)] = cost_p0_c0
                elif i == 0 and j == 1:
                    cm[(i, j)] = cost_p0_c1
                else:
                    # deterministic spread within [cost_min, cost_max]
                    span = cost_max - cost_min
                    frac = ((i + 1) * 7 + (j + 1) * 3) % 11 / 10.0
                    cm[(i, j)] = cost_min + span * frac
        return cm

    cost = cost_matrix()

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, P - 1)
    model.C = pyo.RangeSet(0, C - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= producer_capacity[i]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= contract_demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def min_contrib_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_producers_per_contract[j]

    model.min_contrib_con = pyo.Constraint(model.C, rule=min_contrib_rule)

    def link_upper_rule(m, i, j):
        return m.x[i, j] <= producer_capacity[i] * m.y[i, j]

    model.link_upper_con = pyo.Constraint(model.P, model.C, rule=link_upper_rule)

    def link_lower_rule(m, i, j):
        return m.x[i, j] >= producer_min_delivery[i] * m.y[i, j]

    model.link_lower_con = pyo.Constraint(model.P, model.C, rule=link_lower_rule)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for i in m.P for j in m.C)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}