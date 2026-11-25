import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_matrix = params["cost_matrix"]

    n_prod = len(producer_capacity)
    n_cont = len(contract_demand)

    prod_idx = list(range(n_prod))
    cont_idx = list(range(n_cont))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=prod_idx)
    model.C = pyo.Set(initialize=cont_idx)
    model.PC = pyo.Set(initialize=[(i, j) for i in prod_idx for j in cont_idx], dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j] for (i, j) in mdl.PC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.C) <= producer_capacity[i]

    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.P) >= contract_demand[j]

    model.demand = pyo.Constraint(model.C, rule=demand_rule)

    def contrib_rule(mdl, j):
        return sum(mdl.y[i, j] for i in mdl.P) >= min_contributors[j]

    model.contrib = pyo.Constraint(model.C, rule=contrib_rule)

    def link_min_rule(mdl, i, j):
        return mdl.x[i, j] >= producer_min_delivery[i] * mdl.y[i, j]

    model.link_min = pyo.Constraint(model.PC, rule=link_min_rule)

    def link_max_rule(mdl, i, j):
        return mdl.x[i, j] <= producer_capacity[i] * mdl.y[i, j]

    model.link_max = pyo.Constraint(model.PC, rule=link_max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}