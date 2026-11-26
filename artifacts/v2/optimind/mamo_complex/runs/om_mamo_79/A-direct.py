import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    supply = params["supply"]
    demand = params["demand"]

    n = len(supply)
    regions = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(regions, regions, domain=pyo.NonNegativeIntegers)

    # Zero diagonal: never move within same region
    def diag_rule(mdl, i):
        return mdl.x[i, i] == 0
    model.diag_con = pyo.Constraint(regions, rule=diag_rule)

    # Supply constraints: cannot ship out more than available
    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in regions if j != i) <= supply[i]
    model.supply_con = pyo.Constraint(regions, rule=supply_rule)

    # Demand constraints: incoming + own supply must meet demand
    def demand_rule(mdl, j):
        return supply[j] + sum(mdl.x[i, j] for i in regions if i != j) >= demand[j]
    model.demand_con = pyo.Constraint(regions, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost_matrix[i][j] * mdl.x[i, j]
                   for i in regions for j in regions if i != j)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}