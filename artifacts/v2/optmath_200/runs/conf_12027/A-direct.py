import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    n_prod = len(capacity)
    n_contract = len(demand)

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, n_prod - 1)
    model.contracts = pyo.RangeSet(0, n_contract - 1)

    model.x = pyo.Var(model.producers, model.contracts, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.producers, model.contracts, domain=pyo.Binary)

    def prod_cap_rule(m, i):
        return sum(m.x[i, j] for j in m.contracts) <= capacity[i]
    model.prod_cap = pyo.Constraint(model.producers, rule=prod_cap_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.producers) >= demand[j]
    model.demand_con = pyo.Constraint(model.contracts, rule=demand_rule)

    def minprod_rule(m, j):
        return sum(m.y[i, j] for i in m.producers) >= min_producers[j]
    model.minprod_con = pyo.Constraint(model.contracts, rule=minprod_rule)

    def link_ub_rule(m, i, j):
        ub = min(capacity[i], demand[j])
        return m.x[i, j] <= ub * m.y[i, j]
    model.link_ub = pyo.Constraint(model.producers, model.contracts, rule=link_ub_rule)

    def link_lb_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.link_lb = pyo.Constraint(model.producers, model.contracts, rule=link_lb_rule)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.producers for j in m.contracts)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}