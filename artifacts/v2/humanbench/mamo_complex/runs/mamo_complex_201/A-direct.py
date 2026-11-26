import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants: nodes and directed edges
    nodes = [1, 2, 3, 4]
    edges = [(1, 2), (1, 3), (2, 3), (2, 4), (3, 4)]
    source = 1
    sink = 4

    capacity = {
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 4): params["capacity_3_4"],
    }

    model = pyo.ConcreteModel()

    model.flow = pyo.Var(edges, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(model.flow[e] for e in edges if e[0] == source),
        sense=pyo.maximize,
    )

    def flow_conservation_rule(model, node):
        outflow = sum(model.flow[e] for e in edges if e[0] == node)
        inflow = sum(model.flow[e] for e in edges if e[1] == node)
        return outflow - inflow == 0

    model.flow_conservation = pyo.Constraint(
        [n for n in nodes if n != source and n != sink],
        rule=flow_conservation_rule,
    )

    def capacity_rule(model, e1, e2):
        return model.flow[e1, e2] <= capacity[(e1, e2)]

    model.capacity_con = pyo.Constraint(edges, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}