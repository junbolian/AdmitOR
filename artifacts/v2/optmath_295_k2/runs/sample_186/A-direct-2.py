import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_matrix = params["cost_matrix"]

    producers = list(range(len(producer_capacity)))
    contracts = list(range(len(contract_demand)))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(i, j) for i in producers for j in contracts],
                        dimen=2)

    # Delivery quantity
    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)

    # Binary: producer i contributes to contract j
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    # Producer capacity
    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in contracts) <= producer_capacity[i]
    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    # Contract demand
    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in producers) >= contract_demand[j]
    model.demand = pyo.Constraint(model.C, rule=demand_rule)

    # Min contributors
    def contrib_rule(mdl, j):
        return sum(mdl.y[i, j] for i in producers) >= min_contributors[j]
    model.contrib = pyo.Constraint(model.C, rule=contrib_rule)

    # Linking: min delivery if contributes, and zero if not
    def link_lo_rule(mdl, i, j):
        return mdl.x[i, j] >= producer_min_delivery[i] * mdl.y[i, j]

    def link_hi_rule(mdl, i, j):
        return mdl.x[i, j] <= producer_capacity[i] * mdl.y[i, j]

    model.link_lo = pyo.Constraint(model.PC, rule=link_lo_rule)
    model.link_hi = pyo.Constraint(model.PC, rule=link_hi_rule)

    # Objective
    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j] for i in producers for j in contracts)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}