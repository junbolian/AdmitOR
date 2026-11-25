import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    demands = params["demands"]

    undirected_edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 6), (2, 3), (2, 6),
        (3, 4), (4, 5), (4, 6), (4, 7), (5, 6),
        (5, 7), (6, 7),
    ]

    arcs = []
    for u, v in undirected_edges:
        arcs.append((u, v))
        arcs.append((v, u))

    arc_list = list(range(len(arcs)))
    node_list = list(range(num_nodes))
    comm_list = list(range(num_commodities))

    # Demands mapping: commodity index -> (source, sink, demand)
    sources = {}
    sinks = {}
    dem_vals = {}
    for key, val in demands.items():
        c = int(key) - 1 if not isinstance(key, int) else key
        if isinstance(val, dict):
            src = val["source"]
            snk = val["sink"]
            dem = val["demand"]
        else:
            src, snk, dem = val[0], val[1], val[2]
        sources[c] = src
        sinks[c] = snk
        dem_vals[c] = dem

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arc_list)
    model.NODE = pyo.Set(initialize=node_list)
    model.COMM = pyo.Set(initialize=comm_list)

    model.flow = pyo.Var(model.COMM, model.ARC, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            arc_unit_costs[a] * m.flow[c, a]
            for c in m.COMM for a in m.ARC
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, a):
        return sum(m.flow[c, a] for c in m.COMM) <= arc_capacities[a]
    model.thermal_limit = pyo.Constraint(model.ARC, rule=cap_rule)

    out_arcs = {i: [] for i in node_list}
    in_arcs = {i: [] for i in node_list}
    for a, (u, v) in enumerate(arcs):
        out_arcs[u].append(a)
        in_arcs[v].append(a)

    def balance_rule(m, c, i):
        outflow = sum(m.flow[c, a] for a in out_arcs[i])
        inflow = sum(m.flow[c, a] for a in in_arcs[i])
        if i == sources[c]:
            return outflow - inflow == dem_vals[c]
        elif i == sinks[c]:
            return inflow - outflow == dem_vals[c]
        else:
            return outflow - inflow == 0
    model.flow_balance = pyo.Constraint(model.COMM, model.NODE, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}