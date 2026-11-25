import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    production_cost = params["production_cost"]
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    min_delivery_per_producer = params["min_delivery_per_producer"]

    num_producers = 6
    num_contracts = 6
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(p, c) for p in producers for c in contracts], dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(production_cost[p][c] * mdl.x[p, c] for p in producers for c in contracts)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(mdl, p):
        return sum(mdl.x[p, c] for c in contracts) <= producer_capacity[p]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(mdl, c):
        return sum(mdl.x[p, c] for p in producers) >= contract_demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def contributors_rule(mdl, c):
        return sum(mdl.y[p, c] for p in producers) >= min_contributors[c]

    model.contributors_con = pyo.Constraint(model.C, rule=contributors_rule)

    def link_upper_rule(mdl, p, c):
        cap = producer_capacity[p]
        return mdl.x[p, c] <= cap * mdl.y[p, c]

    model.link_upper_con = pyo.Constraint(model.PC, rule=link_upper_rule)

    def link_lower_rule(mdl, p, c):
        return mdl.x[p, c] >= min_delivery_per_producer[p] * mdl.y[p, c]

    model.link_lower_con = pyo.Constraint(model.PC, rule=link_lower_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception as exc:
        return {"objective": None, "status": str(exc)}

    return {"objective": obj_val, "status": "optimal"}