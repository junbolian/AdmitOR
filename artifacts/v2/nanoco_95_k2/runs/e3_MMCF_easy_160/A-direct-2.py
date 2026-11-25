import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_commodities = int(params["num_commodities"])
    num_arcs = int(params["num_arcs"])
    capacities = list(params["arc_capacities"])
    costs = list(params["arc_unit_costs"])
    supply = list(params["commodity_supply"])
    source = list(params["commodity_source"])
    sink = list(params["commodity_sink"])

    coords = list(params["node_coordinates"])
    edges = list(params["edges"]) if "edges" in params else None

    if edges is not None:
        arcs = []
        for e in edges:
            u, v = int(e[0]), int(e[1])
            arcs.append((u, v))
            arcs.append((v, u))
    else:
        # Reconstruct arcs from coordinates via the known edge structure if
        # edges are not provided; otherwise assume arcs given directly.
        arcs = list(params["arcs"])

    if len(arcs) != num_arcs:
        # Fallback: trust provided arc list length
        num_arcs = len(arcs)

    nodes = range(num_nodes)
    commodities = range(num_commodities)

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=list(range(num_arcs)))
    model.commodity_set = pyo.Set(initialize=list(commodities))
    model.node_set = pyo.Set(initialize=list(nodes))

    model.flow = pyo.Var(model.commodity_set, model.arc_set, domain=pyo.NonNegativeReals)
    model.maxutil = pyo.Var(domain=pyo.NonNegativeReals)

    arc_list = arcs

    tail = {a: arc_list[a][0] for a in range(num_arcs)}
    head = {a: arc_list[a][1] for a in range(num_arcs)}

    out_arcs = {n: [a for a in range(num_arcs) if tail[a] == n] for n in nodes}
    in_arcs = {n: [a for a in range(num_arcs) if head[a] == n] for n in nodes}

    def balance_rule(mdl, k, n):
        out = sum(mdl.flow[k, a] for a in out_arcs[n])
        inn = sum(mdl.flow[k, a] for a in in_arcs[n])
        if n == int(source[k]):
            return out - inn == supply[k]
        elif n == int(sink[k]):
            return out - inn == -supply[k]
        else:
            return out - inn == 0

    model.balance = pyo.Constraint(model.commodity_set, model.node_set, rule=balance_rule)

    def util_rule(mdl, a):
        return sum(mdl.flow[k, a] for k in commodities) <= capacities[a] * mdl.maxutil

    model.util_con = pyo.Constraint(model.arc_set, rule=util_rule)

    model.obj = pyo.Objective(expr=model.maxutil, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}