import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    nodes = list(range(6))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    source, sink = 0, 5

    def cap_val(i, j):
        return float(capacity[i][j])

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs)
    model.nodes = pyo.Set(initialize=nodes)

    model.x = pyo.Var(
        model.arcs,
        bounds=lambda m, i, j: (0, cap_val(i, j)),
    )

    model.flow_value = pyo.Var(within=pyo.NonNegativeReals)

    def flow_balance(m, n):
        inflow = sum(m.x[i, j] for (i, j) in arcs if j == n)
        outflow = sum(m.x[i, j] for (i, j) in arcs if i == n)
        if n == source:
            return inflow - outflow == -m.flow_value
        elif n == sink:
            return inflow - outflow == m.flow_value
        else:
            return inflow - outflow == 0

    model.balance_con = pyo.Constraint(model.nodes, rule=flow_balance)

    model.total_flow = pyo.Objective(
        expr=model.flow_value, sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}