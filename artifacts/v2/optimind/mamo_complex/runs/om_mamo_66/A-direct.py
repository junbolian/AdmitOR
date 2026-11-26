import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(6))
    source = 0
    sink = 5

    # Build arc list from provided capacity params
    arc_keys = [
        "0_1", "0_2", "0_3", "0_4", "0_5",
        "1_0", "1_2", "1_3", "1_5",
        "2_0", "2_1", "2_3", "2_4", "2_5",
        "3_0", "3_1", "3_2", "3_5",
        "4_0", "4_1", "4_2", "4_3", "4_5",
        "5_0", "5_1", "5_2", "5_3", "5_4",
    ]
    arcs = []
    for key in arc_keys:
        parts = key.split("_")
        i = int(parts[0])
        j = int(parts[1])
        idx = i * 6 + j
        arcs.append((i, j, idx))

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=[a[2] for a in arcs])
    model.N = pyo.Set(initialize=nodes)

    cap_dict = {}
    tail_dict = {}
    head_dict = {}
    for (i, j, idx) in arcs:
        cap_dict[idx] = float(params["capacity_" + str(i) + "_" + str(j)])
        tail_dict[idx] = i
        head_dict[idx] = j

    model.cap = pyo.Param(model.A, initialize=cap_dict, within=pyo.NonNegativeReals)

    model.flow = pyo.Var(model.A, within=pyo.NonNegativeReals)

    def flow_upper_bound(mdl, a):
        return mdl.flow[a] <= mdl.cap[a]
    model.flow_upper = pyo.Constraint(model.A, rule=flow_upper_bound)

    # Flow conservation: net outflow from source = -net inflow, sink absorbs, others balance
    def conservation_rule(mdl, n):
        out_flow = sum(mdl.flow[a] for a in mdl.A if tail_dict[a] == n)
        in_flow = sum(mdl.flow[a] for a in mdl.A if head_dict[a] == n)
        if n == source:
            return out_flow - in_flow >= 0
        elif n == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0
    model.flow_conservation = pyo.Constraint(model.N, rule=conservation_rule)

    # Objective: maximize net flow out of source (equivalently into sink)
    def obj_rule(mdl):
        return sum(mdl.flow[a] for a in mdl.A if tail_dict[a] == source) \
             - sum(mdl.flow[a] for a in mdl.A if head_dict[a] == source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible or failed: " + str(exc)[:100]}