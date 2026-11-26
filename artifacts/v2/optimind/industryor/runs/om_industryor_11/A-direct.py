import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    volume = params["volume"]
    demand = params["demand"]
    unit_cost = params["unit_cost"]
    setup_cost = params["setup_cost"]

    n = len(volume)
    types = list(range(n))

    model = pyo.ConcreteModel()

    # x[i] = quantity of type i produced
    model.x = pyo.Var(types, domain=pyo.NonNegativeReals)
    # y[i] = 1 if type i equipment activated
    model.y = pyo.Var(types, domain=pyo.Binary)

    # Demand coverage: for each demand-type j, total production of containers
    # with volume >= volume[j] must cover demand[j]
    # (fill allowed only from larger-or-equal types)
    def demand_rule(m, j):
        return sum(m.x[i] for i in types if volume[i] >= volume[j]) >= demand[j]

    model.demand_con = pyo.Constraint(types, rule=demand_rule)

    # Linking: if produce > 0 then activate equipment
    big_m = sum(demand)
    def link_rule(m, i):
        return m.x[i] <= big_m * m.y[i]

    model.link_con = pyo.Constraint(types, rule=link_rule)

    # Objective: variable cost + setup cost
    model.total_cost = pyo.Objective(
        expr=sum(unit_cost[i] * model.x[i] for i in types)
        + sum(setup_cost * model.y[i] for i in types),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}