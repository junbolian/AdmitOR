import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]
    capacities = params["capacities"]

    num_warehouses = len(supplies)
    num_stores = len(demands)

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, num_warehouses - 1)
    model.S = pyo.RangeSet(0, num_stores - 1)

    model.x = pyo.Var(model.W, model.S, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacities[i][j]
    model.cap_con = pyo.Constraint(model.W, model.S, rule=cap_rule)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.S) == supplies[i]
    model.supply_con = pyo.Constraint(model.W, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.W) == demands[j]
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def obj_rule(m):
        return sum(transport_costs[i][j] * m.x[i, j] for i in m.W for j in m.S)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible or failed: " + str(exc)}