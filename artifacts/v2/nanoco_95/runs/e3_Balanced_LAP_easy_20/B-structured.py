# IR: {"sets":{"agents":[0,1,2,3,4,5],"tickets":[0,1,2,3,4,5]},"params":{"cost":{"source":"params['cost']","indices":["agents","tickets"]}},"variables":{"x":{"indices":["agents","tickets"],"type":"binary"}},"constraints":["For each agent i: sum_j x[i,j] == 1","For each ticket j: sum_i x[i,j] == 1"],"objective":{"sense":"minimize","expression":"sum_i sum_j cost[i,j] * x[i,j]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.agents = pyo.RangeSet(0, 5)
    model.tickets = pyo.RangeSet(0, 5)

    model.cost = pyo.Param(
        model.agents,
        model.tickets,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.agents
            for j in model.tickets
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.agents, model.tickets, domain=pyo.Binary)

    def agent_assignment_rule(instance, i):
        return sum(instance.x[i, j] for j in instance.tickets) == 1

    model.agent_assignment = pyo.Constraint(
        model.agents, rule=agent_assignment_rule
    )

    def ticket_assignment_rule(instance, j):
        return sum(instance.x[i, j] for i in instance.agents) == 1

    model.ticket_assignment = pyo.Constraint(
        model.tickets, rule=ticket_assignment_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.agents
            for j in model.tickets
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}