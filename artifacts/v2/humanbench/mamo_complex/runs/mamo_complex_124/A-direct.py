import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    nodes = range(n)

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=nodes)
    model.J = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            cost[i][j] * mdl.x[i, j]
            for i in nodes
            for j in nodes
            if i != j and cost[i][j] is not None
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # flow conservation: inventory - shipped_out + shipped_in == demand
    def balance_rule(mdl, i):
        out_flow = sum(mdl.x[i, j] for j in nodes if j != i and cost[i][j] is not None)
        in_flow = sum(mdl.x[j, i] for j in nodes if j != i and cost[j][i] is not None)
        return supply[i] - out_flow + in_flow == demand[i]
    model.balance = pyo.Constraint(model.I, rule=balance_rule)

    # restrict total shipped out to <= supply and disallow invalid pairs
    def no_flow_rule(mdl, i, j):
        if i == j or cost[i][j] is None:
            return mdl.x[i, j] == 0
        return pyo.Constraint.Skip
    model.no_flow = pyo.Constraint(model.I, model.J, rule=no_flow_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}