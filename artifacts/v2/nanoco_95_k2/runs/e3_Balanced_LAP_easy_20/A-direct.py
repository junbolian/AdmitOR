import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost = params["cost"]
    n = len(cost)

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, n - 1)
    model.J = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def agent_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == 1
    model.agent_con = pyo.Constraint(model.I, rule=agent_rule)

    def ticket_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == 1
    model.ticket_con = pyo.Constraint(model.J, rule=ticket_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solver failed"}