import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 16
    root = 0
    turbines = list(range(1, n))
    max_per_feeder = params["max_turbines_per_feeder"]
    cost = params["cable_cost_matrix"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n - 1)
    model.turbines = pyo.Set(initialize=turbines)

    model.arcs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n) if i != j],
        dimen=2,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Each turbine has exactly one incoming arc
    def inflow_rule(m, j):
        return sum(m.x[i, j] for i in m.nodes if i != j) == 1

    model.inflow = pyo.Constraint(model.turbines, rule=inflow_rule)

    # No arcs into root
    def no_in_root_rule(m):
        return sum(m.x[i, root] for i in m.nodes if i != root) == 0

    model.no_in_root = pyo.Constraint(rule=no_in_root_rule)

    # Flow variables for connectivity / capacity
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_balance_rule(m, j):
        inflow = sum(m.f[i, j] for i in m.nodes if i != j)
        outflow = sum(m.f[j, k] for k in m.nodes if k != j)
        return inflow - outflow == 1

    model.flow_balance = pyo.Constraint(model.turbines, rule=flow_balance_rule)

    def flow_cap_rule(m, i, j):
        return m.f[i, j] <= (n - 1) * m.x[i, j]

    model.flow_cap = pyo.Constraint(model.arcs, rule=flow_cap_rule)

    # Capacity constraint on each feeder string out of root
    def root_arc_cap_rule(m, j):
        return m.f[root, j] <= max_per_feeder * m.x[root, j]

    model.root_arc_cap = pyo.Constraint(model.turbines, rule=root_arc_cap_rule)

    def objective_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}