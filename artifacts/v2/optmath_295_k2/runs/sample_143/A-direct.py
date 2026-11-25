import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_supply = len(supply)
    n_demand = len(demand)

    cost_mat = [[cost[i * n_demand + j] for j in range(n_demand)] for i in range(n_supply)]
    cap_mat = [[capacity[i * n_demand + j] for j in range(n_demand)] for i in range(n_supply)]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_supply - 1)
    model.J = pyo.RangeSet(0, n_demand - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= cap_mat[i][j]

    model.cap_con = pyo.Constraint(model.I, model.J, rule=cap_rule)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) == supply[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost_mat[i][j] * mdl.x[i, j] for i in mdl.I for j in mdl.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}