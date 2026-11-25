import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    def cost(i, j):
        return params["arc_cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Node 0: net outflow = supply_node_0
    model.bal0 = pyo.Constraint(
        expr=sum(model.x[0, j] for j in nodes if j != 0)
        - sum(model.x[i, 0] for i in nodes if i != 0)
        == params["supply_node_0"]
    )

    # Node 6: net inflow = demand_node_6
    model.bal6 = pyo.Constraint(
        expr=sum(model.x[i, 6] for i in nodes if i != 6)
        - sum(model.x[6, j] for j in nodes if j != 6)
        == params["demand_node_6"]
    )

    # Intermediate hubs 1..5: balanced flow (inflow - outflow = 0)
    model.bal_mid = pyo.Constraint(
        [k for k in range(1, 6)],
        rule=lambda m, k: sum(m.x[i, k] for i in nodes if i != k)
        - sum(m.x[k, j] for j in nodes if j != k)
        == params["balance_nodes_1_5"],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}