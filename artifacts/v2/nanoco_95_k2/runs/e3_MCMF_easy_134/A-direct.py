import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Index sets (structural constants)
    nodes = list(range(10))
    arcs = [
        (0, 1), (1, 2), (1, 4), (1, 5), (1, 7),
        (2, 3), (3, 4), (4, 5), (4, 8), (4, 9),
        (5, 6), (5, 7), (6, 7), (7, 8), (8, 9),
    ]
    arc_names = {
        (0, 1): "0_1", (1, 2): "1_2", (1, 4): "1_4", (1, 5): "1_5", (1, 7): "1_7",
        (2, 3): "2_3", (3, 4): "3_4", (4, 5): "4_5", (4, 8): "4_8", (4, 9): "4_9",
        (5, 6): "5_6", (5, 7): "5_7", (6, 7): "6_7", (7, 8): "7_8", (8, 9): "8_9",
    }

    cap = {a: params["capacity_" + arc_names[a]] for a in arcs}
    cost = {a: params["cost_" + arc_names[a]] for a in arcs}

    source, sink = 0, 9

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    # Flow conservation at intermediate nodes
    def balance_rule(m, n):
        if n == source or n == sink:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == n)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == n)
        return inflow == outflow
    model.balance_con = pyo.Constraint(nodes, rule=balance_rule)

    # Net flow from source to sink
    def source_expr(m):
        return sum(m.flow[source, j] for (i, j) in arcs if i == source)
    model.supply = pyo.Expression(rule=source_expr)

    def sink_expr(m):
        return sum(m.flow[i, sink] for (i, j) in arcs if j == sink)
    model.demand = pyo.Expression(rule=sink_expr)

    model.link_con = pyo.Constraint(expr=model.supply == model.demand)

    # --- Stage 1: maximize flow ---
    model.obj1 = pyo.Objective(expr=model.supply, sense=pyo.maximize)
    Highs().solve(model)
    max_flow = float(pyo.value(model.supply))

    # --- Stage 2: minimize cost subject to max flow ---
    model.flow_fix = pyo.Constraint(expr=model.supply == max_flow)
    model.del_component(model.obj1)
    model.obj2 = pyo.Objective(
        expr=sum(cost[(i, j)] * model.flow[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )
    Highs().solve(model)

    obj_val = float(pyo.value(model.obj2))
    return {"objective": obj_val, "status": "optimal"}