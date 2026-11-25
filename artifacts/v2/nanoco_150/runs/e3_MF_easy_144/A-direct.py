import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    # node_coordinates does not affect flow feasibility or objective.

    edges = [
        (0, 1), (1, 2), (1, 4), (1, 5), (1, 7),
        (2, 3), (3, 4), (4, 5), (4, 8), (4, 9),
        (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
    ]
    num_nodes = 10
    source = 0
    sink = 9

    edge_index = list(range(len(edges)))
    edge_cap = {i: capacities[i] for i in edge_index}
    edge_cost = {i: unit_costs[i] for i in edge_index}
    edge_from = {i: edges[i][0] for i in edge_index}
    edge_to = {i: edges[i][1] for i in edge_index}

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=edge_index)
    model.NODES = pyo.Set(initialize=range(num_nodes))

    model.flow = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals,
                         bounds=lambda m, i: (0.0, float(edge_cap[i])))

    out_edges = {n: [] for n in range(num_nodes)}
    in_edges = {n: [] for n in range(num_nodes)}
    for i in edge_index:
        out_edges[edge_from[i]].append(i)
        in_edges[edge_to[i]].append(i)

    def flow_balance_rule(m, n):
        inflow = sum(m.flow[i] for i in in_edges[n])
        outflow = sum(m.flow[i] for i in out_edges[n])
        return inflow == outflow

    model.intermediate = pyo.Set(
        initialize=[n for n in range(num_nodes) if n != source and n != sink]
    )
    model.flow_balance = pyo.Constraint(model.intermediate, rule=flow_balance_rule)

    model.total_delivered = pyo.Expression(
        expr=sum(model.flow[i] for i in in_edges[sink])
    )

    model.obj = pyo.Objective(expr=model.total_delivered, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}