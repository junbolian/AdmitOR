import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    n_products = len(demand)
    n_months = len(demand[0])
    products = range(n_products)
    months = range(n_months)

    # Max production = cumulative demand from month t onward
    max_prod = {}
    for i in products:
        for t in months:
            max_prod[i, t] = sum(demand[i][k] for k in range(t, n_months))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=list(products))
    model.T = pyo.Set(initialize=list(months))

    model.x = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, model.T, domain=pyo.Binary)
    model.inv = pyo.Var(model.I, model.T, domain=pyo.NonNegativeReals)

    def prod_cost_rule(m):
        return sum(production_cost[i][t] * m.x[i, t]
                   for i in m.I for t in m.T)

    def setup_cost_rule(m):
        return sum(setup_cost[i][t] * m.y[i, t]
                   for i in m.I for t in m.T)

    def hold_cost_rule(m):
        return sum(holding_cost[i] * m.inv[i, t]
                   for i in m.I for t in m.T)

    model.prod_cost = pyo.Expression(rule=prod_cost_rule)
    model.setup_cost_expr = pyo.Expression(rule=setup_cost_rule)
    model.hold_cost = pyo.Expression(rule=hold_cost_rule)

    def obj_rule(m):
        return (prod_cost_rule(m) + setup_cost_rule(m) + hold_cost_rule(m))

    def capacity_rule(m, t):
        return sum(capacity_consumption[i] * m.x[i, t]
                   for i in m.I) <= capacity[t]

    model.capacity_con = pyo.Constraint(model.T, rule=capacity_rule)

    def link_rule(m, i, t):
        return m.x[i, t] <= max_prod[i, t] * m.y[i, t]

    model.link_con = pyo.Constraint(model.I, model.T, rule=link_rule)

    def balance_rule(m, i, t):
        cum_prod = sum(m.x[i, k] for k in range(0, t + 1))
        cum_dem = sum(demand[i][k] for k in range(0, t + 1))
        return cum_prod + m.inv[i, t] == cum_dem

    model.balance_con = pyo.Constraint(model.I, model.T, rule=balance_rule)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}