import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # capacity may be provided under different keys; locate the mapping of arcs -> capacity
    capacity = None
    if "capacity" in params:
        capacity = params["capacity"]
    else:
        for key, val in params.items():
            if isinstance(val, dict):
                # Heuristic: a dict whose items look like arc->number pairs
                is_arc_map = False
                try:
                    for k, v in val.items():
                        if isinstance(k, (tuple, list)) and len(k) == 2 and isinstance(v, (int, float)):
                            is_arc_map = True
                            break
                except Exception:
                    is_arc_map = False
                if is_arc_map:
                    capacity = val
                    break

    if capacity is None:
        return {"objective": None, "status": "missing capacity data"}

    # Normalize keys to tuples of ints
    arc_caps = {}
    for k, v in capacity.items():
        if isinstance(k, (tuple, list)) and len(k) == 2:
            i, j = int(k[0]), int(k[1])
            arc_caps[(i, j)] = float(v)
        elif isinstance(k, str):
            # support strings like "0,1" or "0-1"
            s = k.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
            parts = s.replace("->", ",").replace("-", ",").replace(";", ",").replace(" ", ",").split(",")
            parts = [p for p in parts if p != ""]
            if len(parts) == 2:
                i, j = int(parts[0]), int(parts[1])
                arc_caps[(i, j)] = float(v)

    nodes = list(range(9))
    source = 0
    sink = 8

    arcs = [(i, j) for (i, j), c in arc_caps.items() if i != j and c > 0]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def flow_balance_rule(m, v):
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == v)
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == v)
        if v == source:
            return pyo.Constraint.Skip
        elif v == sink:
            return pyo.Constraint.Skip
        return outflow - inflow == 0

    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= arc_caps[(i, j)]

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def obj_rule(m):
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == source)
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == source)
        return outflow - inflow

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or unbounded"}

    return {"objective": obj_val, "status": "optimal"}