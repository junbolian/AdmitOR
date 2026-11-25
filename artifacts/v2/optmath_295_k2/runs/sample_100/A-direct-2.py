import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]

    n_prod = len(capacity)
    n_cont = len(demand)
    producers = range(n_prod)
    contracts = range(n_cont)

    model = pyo.ConcreteModel()

    model.producers = pyo.Set(initialize=list(producers))
    model.contracts = pyo.Set(initialize=list(contracts))
    model.pairs = pyo.Set(initialize=[(i, j) for i in producers for j in contracts], dimen=2)

    model.x = pyo.Var(model.pairs, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.pairs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in producers for j in contracts),
        sense=pyo.minimize,
    )

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in contracts) <= capacity[i]

    model.capacity_con = pyo.Constraint(model.producers, rule=capacity_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in producers) >= demand[j]

    model.demand_con = pyo.Constraint(model.contracts, rule=demand_rule)

    def contributors_rule(m, j):
        return sum(m.y[i, j] for i in producers) >= min_contributors[j]

    model.contributors_con = pyo.Constraint(model.contracts, rule=contributors_rule)

    def link_ub_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]

    model.link_ub_con = pyo.Constraint(model.pairs, rule=link_ub_rule)

    def link_lb_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.link_lb_con = pyo.Constraint(model.pairs, rule=link_lb_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}