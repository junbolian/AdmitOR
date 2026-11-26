import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    regions = list(range(6))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=regions)
    model.J = pyo.Set(initialize=regions)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def cost_rule(m):
        return sum(transport_cost[i][j] * m.x[i, j]
                   for i in m.I for j in m.J if i != j)
    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    # Each region must end with at least its required demand:
    # initial supply - shipments out + shipments in >= demand
    def balance_rule(m, i):
        return (supply[i]
                - sum(m.x[i, j] for j in m.J if j != i)
                + sum(m.x[j, i] for j in m.J if j != i)
                >= demand[i])
    model.balance = pyo.Constraint(model.I, rule=balance_rule)

    # No self-shipment
    def no_self_rule(m, i):
        return m.x[i, i] == 0
    model.no_self = pyo.Constraint(model.I, rule=no_self_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}