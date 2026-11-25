import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    nodes = list(range(N))

    # Build directed arcs (i, j), i != j
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Cost key helper: cost_i_j
    def cost_of(i, j):
        return params["cost_{}_{}".format(i, j)]

    supply = {i: 0.0 for i in nodes}
    supply[0] = params["supply_node0"]
    supply[5] = -params["demand_node5"]  # demand at node 5 -> net outflow = -demand

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(cost_of(i, j) * m.x[i, j] for (i, j) in m.ARCS)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def flow_balance_rule(m, n):
        outflow = sum(m.x[n, j] for j in nodes if j != n)
        inflow = sum(m.x[i, n] for i in nodes if i != n)
        return outflow - inflow == supply[n]

    model.FlowBalance = pyo.Constraint(nodes, rule=flow_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}