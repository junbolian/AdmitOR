import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)

    model = pyo.ConcreteModel()

    model.OA = pyo.Set(initialize=list(range(n_origins)))
    model.DB = pyo.Set(initialize=list(range(n_dests)))

    model.x = pyo.Var(model.OA, model.DB, within=pyo.NonNegativeReals)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.DB) == supply[i]

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.OA) == demand[j]

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity[i][j]

    model.supply_con = pyo.Constraint(model.OA, rule=supply_rule)
    model.demand_con = pyo.Constraint(model.DB, rule=demand_rule)
    model.cap_con = pyo.Constraint(model.OA, model.DB, rule=cap_rule)

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for i in mdl.OA for j in mdl.DB)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}