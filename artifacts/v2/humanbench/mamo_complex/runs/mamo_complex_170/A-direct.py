import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_data_centers"])
    nodes = list(range(n))
    source = 0
    sink = n - 1

    # Directed edges: any i != j, with i not the sink and j not the source.
    # Missing capacity_*_* keys in params are treated as capacity 0.
    edge_keys = []
    for i in nodes:
        if i == sink:
            continue
        for j in nodes:
            if j == source:
                continue
            if i == j:
                continue
            edge_keys.append((i, j))

    cap = {}
    for (i, j) in edge_keys:
        pname = "capacity_%d_%d" % (i, j)
        cap[(i, j)] = params.get(pname, 0.0)

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edge_keys, dimen=2)

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.edges, rule=cap_rule)

    # Flow conservation at every node except source and sink
    intermediate = [k for k in nodes if k != source and k != sink]

    def balance_rule(mdl, k):
        out_flow = sum(mdl.flow[k, j] for j in nodes if (k, j) in cap)
        in_flow = sum(mdl.flow[i, k] for i in nodes if (i, k) in cap)
        return out_flow - in_flow == 0
    model.balance_con = pyo.Constraint(intermediate, rule=balance_rule)

    # Objective: maximize net flow out of source
    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in nodes if (source, j) in cap)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}