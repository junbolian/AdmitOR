import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)
    m = len(cost[0])

    model = pyo.ConcreteModel()
    model.agents = pyo.RangeSet(0, n - 1)
    model.tickets = pyo.RangeSet(0, m - 1)
    model.x = pyo.Var(model.agents, model.tickets, domain=pyo.Binary)

    model.agent_constraint = pyo.Constraint(
        model.agents,
        rule=lambda model, i: sum(model.x[i, j] for j in model.tickets) == 1,
    )
    model.ticket_constraint = pyo.Constraint(
        model.tickets,
        rule=lambda model, j: sum(model.x[i, j] for i in model.agents) == 1,
    )
    model.total_cost = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j]
                 for i in model.agents for j in model.tickets),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}