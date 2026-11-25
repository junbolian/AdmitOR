import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_producers - 1)
    model.C = pyo.RangeSet(0, num_contracts - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(production_cost[p][c] * m.x[p, c] for p in m.P for c in m.C)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= producer_capacity[p]
    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= contract_demand[c]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def contributors_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_contributors[c]
    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    def linking_lb_rule(m, p, c):
        return m.x[p, c] >= min_delivery_per_producer[p] * m.y[p, c]
    model.linking_lb_con = pyo.Constraint(model.P, model.C, rule=linking_lb_rule)

    def linking_ub_rule(m, p, c):
        return m.x[p, c] <= producer_capacity[p] * m.y[p, c]
    model.linking_ub_con = pyo.Constraint(model.P, model.C, rule=linking_ub_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}