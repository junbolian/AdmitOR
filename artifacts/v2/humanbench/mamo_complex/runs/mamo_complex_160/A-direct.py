import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    edge_capacities = params["edge_capacities"]

    nodes = list(range(num_cities))

    edges = []
    for i in nodes:
        for j in nodes:
            if i != j:
                edges.append((i, j))

    cap = {}
    for edge, c in zip(edges, edge_capacities):
        cap[edge] = float(c)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def flow_balance_rule(mdl, i):
        inflow = sum(mdl.flow[j, i] for j in nodes if j != i)
        outflow = sum(mdl.flow[i, j] for j in nodes if j != i)
        if i == source_node:
            return outflow - inflow == mdl.supply
        elif i == sink_node:
            return inflow - outflow == mdl.supply
        else:
            return inflow - outflow == 0

    model.supply = pyo.Var(domain=pyo.NonNegativeReals)

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]

    model.capacity = pyo.Constraint(model.edges, rule=capacity_rule)

    model.obj = pyo.Objective(expr=model.supply, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}