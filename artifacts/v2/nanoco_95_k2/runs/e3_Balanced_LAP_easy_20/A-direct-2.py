import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    n = len(cost)
    m = len(cost[0])

    model = pyo.ConcreteModel()
    model.agents = pyo.RangeSet(n)
    model.tickets = pyo.RangeSet(m)

    model.x = pyo.Var(model.agents, model.tickets, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost[i][j] * model.x[i + 1, j + 1]
                   for i in range(n) for j in range(m))
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.agent_constraints = pyo.Constraint(
        model.agents,
        rule=lambda model, i: sum(model.x[i, j] for j in model.tickets) == 1
    )
    model.ticket_constraints = pyo.Constraint(
        model.tickets,
        rule=lambda model, j: sum(model.x[i, j] for i in model.agents) == 1
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}