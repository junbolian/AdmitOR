import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])

    # Conflict edges: (u, v, required separation) read from params
    edge_pairs = [(0, 1), (0, 7), (1, 4), (1, 7), (4, 5)]
    edge_buffers = {
        (0, 1): params["safety_buffer_0_1"],
        (0, 7): params["safety_buffer_0_7"],
        (1, 4): params["safety_buffer_1_4"],
        (1, 7): params["safety_buffer_1_7"],
        (4, 5): params["safety_buffer_4_5"],
    }

    model = pyo.ConcreteModel()

    model.AIRCRAFT = pyo.RangeSet(0, num_nodes - 1)
    model.EDGES = pyo.Set(initialize=edge_pairs, dimen=2)

    # Gate slot for each aircraft (non-negative integers)
    model.x = pyo.Var(model.AIRCRAFT, domain=pyo.NonNegativeIntegers)

    # Maximum gate slot index utilized
    model.z = pyo.Var(domain=pyo.NonNegativeIntegers)

    # z upper-bounds every assigned slot
    def _bound_rule(m, i):
        return m.z >= m.x[i]

    model.bound_con = pyo.Constraint(model.AIRCRAFT, rule=_bound_rule)

    # Absolute separation constraints via disjunction-free linearization:
    # x[u] - x[v] >= d  OR  x[v] - x[u] >= d
    # Handled with binary selectors.
    model.PAIRS = pyo.Set(initialize=edge_pairs, dimen=2)
    model.sel = pyo.Var(model.PAIRS, domain=pyo.Binary)

    def _sep_rule(m, u, v):
        d = edge_buffers[(u, v)]
        # If sel == 0: x[u] - x[v] >= d ; if sel == 1: x[v] - x[u] >= d
        big = num_nodes + max(edge_buffers.values())
        return m.x[u] - m.x[v] >= d - big * m.sel[(u, v)]

    def _sep_rule_rev(m, u, v):
        d = edge_buffers[(u, v)]
        big = num_nodes + max(edge_buffers.values())
        return m.x[v] - m.x[u] >= d - big * (1 - m.sel[(u, v)])

    model.sep_a = pyo.Constraint(model.PAIRS, rule=_sep_rule)
    model.sep_b = pyo.Constraint(model.PAIRS, rule=_sep_rule_rev)

    # Objective: minimize the highest gate slot index used
    def _obj_rule(m):
        return m.z

    model.obj = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}