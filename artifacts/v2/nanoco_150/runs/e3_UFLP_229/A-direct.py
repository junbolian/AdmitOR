import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_incidents = 19
    num_hubs = 5

    fixed_cost = [
        params["fixed_cost_hub_0"],
        params["fixed_cost_hub_1"],
        params["fixed_cost_hub_2"],
        params["fixed_cost_hub_3"],
        params["fixed_cost_hub_4"],
    ]

    response_time = params["response_time"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, num_incidents - 1)
    model.J = pyo.RangeSet(0, num_hubs - 1)

    model.y = pyo.Var(model.J, domain=pyo.Binary)
    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    # Objective is stored on a named component so it can be retrieved via pyo.value
    model.total_cost = pyo.Objective(
        expr=sum(fixed_cost[j] * model.y[j] for j in model.J)
        + sum(response_time[i][j] * model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == 1

    model.assign_con = pyo.Constraint(model.I, rule=assign_rule)

    def link_rule(m, i, j):
        return m.x[i, j] <= m.y[j]

    model.link_con = pyo.Constraint(model.I, model.J, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}