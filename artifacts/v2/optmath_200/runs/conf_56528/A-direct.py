import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node6 = params["demand_node6"]
    cost_matrix = params["cost_matrix"]

    nodes = list(range(7))

    model = pyo.ConcreteModel()

    # Binary route decision variables for all i != j
    model.route = pyo.Var(
        [(i, j) for i in nodes for j in nodes if i != j],
        domain=pyo.Binary,
    )

    # Objective: minimize total transportation cost
    def obj_rule(mdl):
        return sum(
            cost_matrix[i][j] * mdl.route[i, j]
            for i in nodes
            for j in nodes
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance constraints
    def balance_rule(mdl, k):
        outflow = sum(mdl.route[k, j] for j in nodes if j != k)
        inflow = sum(mdl.route[i, k] for i in nodes if i != k)
        net_out = outflow - inflow
        if k == 0:
            return net_out == supply_node0
        if k == 6:
            return -(net_out) == demand_node6
        return net_out == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}