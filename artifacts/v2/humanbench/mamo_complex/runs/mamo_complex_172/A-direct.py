import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 9
    source = 0
    sink = 8

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    # Flow variables on each directed arc, bounded by arc capacity
    model.Flow = pyo.Var(arcs, domain=pyo.NonNegativeReals)

    def flow_bound_rule(model, i, j):
        return model.Flow[i, j] <= capacity[i][j]
    model.FlowBoundCon = pyo.Constraint(arcs, rule=flow_bound_rule)

    # Flow conservation at every node
    def flow_conservation_rule(model, k):
        inflow = sum(model.Flow[i, k] for i in nodes if i != k)
        outflow = sum(model.Flow[k, j] for j in nodes if j != k)
        if k == source:
            return outflow - inflow == model.TotalFlow
        elif k == sink:
            return inflow - outflow == model.TotalFlow
        else:
            return inflow - outflow == 0

    model.TotalFlow = pyo.Var(domain=pyo.NonNegativeReals)
    model.FlowConservationCon = pyo.Constraint(nodes, rule=flow_conservation_rule)

    # Maximize net flow from source to sink
    model.Objective = pyo.Objective(expr=model.TotalFlow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.Objective))
    return {'objective': obj_val, 'status': 'optimal'}