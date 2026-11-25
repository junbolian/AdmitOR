import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_factories = int(params["num_factories"])
    num_months = int(params["num_months"])

    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    factories = list(range(num_factories))
    months = list(range(num_months))

    model = pyo.ConcreteModel()

    model.FACT = pyo.Set(initialize=factories, ordered=True)
    model.MONTH = pyo.Set(initialize=months, ordered=True)
    model.FM = pyo.Set(initialize=[(f, t) for f in factories for t in months], dimen=2)

    model.run_flag = pyo.Var(model.FM, domain=pyo.Binary)
    model.produce = pyo.Var(model.FM, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            activation_cost[f] * m.run_flag[f, t]
            + production_cost[f] * m.produce[f, t]
            for f, t in m.FM
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(m, f, t):
        return m.produce[f, t] >= min_production[f] * m.run_flag[f, t]

    model.min_prod_con = pyo.Constraint(model.FM, rule=min_prod_rule)

    def max_prod_rule(m, f, t):
        return m.produce[f, t] <= max_production[f] * m.run_flag[f, t]

    model.max_prod_con = pyo.Constraint(model.FM, rule=max_prod_rule)

    def demand_rule(m, t):
        return sum(m.produce[f, t] for f in m.FACT) >= demand[t]

    model.demand_con = pyo.Constraint(model.MONTH, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}