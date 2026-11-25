import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(params["edge_cost_{}_{}".format(i, j)] * model.x[(i, j)]
                 for (i, j) in arcs),
        sense=pyo.minimize
    )

    def balance_rule(m, n):
        inflow = sum(m.x[(i, n)] for i in nodes if i != n)
        outflow = sum(m.x[(n, j)] for j in nodes if j != n)
        if n == 0:
            return outflow - inflow == params["net_supply_node_0"]
        elif n == 7:
            return inflow - outflow == params["net_demand_node_7"]
        else:
            return inflow - outflow == params["flow_balance_intermediate"]

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}