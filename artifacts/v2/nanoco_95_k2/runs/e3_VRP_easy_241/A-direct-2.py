import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    K = params["num_vehicles"]
    n = len(dist)            # number of nodes including depot (9)
    customers = list(range(1, n))  # nodes 1..8

    model = pyo.ConcreteModel()

    # Sets
    model.V = pyo.Set(initialize=list(range(n)))          # all nodes
    model.C = pyo.Set(initialize=customers)               # customers
    model.K = pyo.Set(initialize=list(range(K)))          # vehicles

    # Arc set: no self loops
    def arc_init(m):
        return [(i, j) for i in range(n) for j in range(n) if i != j]
    model.A = pyo.Set(initialize=arc_init, dimen=2)

    # x[i,j,k] = 1 if vehicle k travels arc i->j
    model.x = pyo.Var(model.A, model.K, domain=pyo.Binary)

    # Objective: minimize total distance
    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j, k] for (i, j) in m.A for k in m.K)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer is visited exactly once (one incoming arc)
    def visit_in_rule(m, j):
        return sum(m.x[i, j, k] for i in m.V if i != j for k in m.K) == 1
    model.visit_in = pyo.Constraint(model.C, rule=visit_in_rule)

    # Flow conservation at each customer
    def flow_rule(m, j, k):
        return (sum(m.x[i, j, k] for i in m.V if i != j)
                - sum(m.x[j, i, k] for i in m.V if i != j)) == 0
    model.flow = pyo.Constraint(model.C, model.K, rule=flow_rule)

    # Each vehicle leaves the depot at most once
    def depot_out_rule(m, k):
        return sum(m.x[0, j, k] for j in m.V if j != 0) <= 1
    model.depot_out = pyo.Constraint(model.K, rule=depot_out_rule)

    # Each vehicle returns to the depot at most once
    def depot_in_rule(m, k):
        return sum(m.x[i, 0, k] for i in m.V if i != 0) <= 1
    model.depot_in = pyo.Constraint(model.K, rule=depot_in_rule)

    # Number of vehicles leaving depot equals number returning (for each k)
    def depot_balance_rule(m, k):
        return (sum(m.x[0, j, k] for j in m.V if j != 0)
                - sum(m.x[i, 0, k] for i in m.V if i != 0)) == 0
    model.depot_balance = pyo.Constraint(model.K, rule=depot_balance_rule)

    # Require use of exactly K vehicles (each vehicle must depart exactly once)
    # Since fleet must be utilized, enforce exactly one departure per vehicle.
    def use_vehicle_rule(m, k):
        return sum(m.x[0, j, k] for j in m.V if j != 0) == 1
    model.use_vehicle = pyo.Constraint(model.K, rule=use_vehicle_rule)

    # MTZ subtour elimination
    # u[j,k] = position of customer j in route of vehicle k (order counter)
    model.u = pyo.Var(model.C, model.K, domain=pyo.NonNegativeReals)

    bigM = 2 * n

    def mtz_rule(m, i, j, k):
        if i == j:
            return pyo.Constraint.Skip
        return (m.u[i, k] - m.u[j, k] + bigM * m.x[i, j, k]
                <= bigM - 1)
    model.mtz = pyo.Constraint(model.C, model.C, model.K, rule=mtz_rule)

    # Position bounds for each customer on each vehicle
    def u_bound_rule(m, j, k):
        return m.u[j, k] <= n - 1
    model.u_bound = pyo.Constraint(model.C, model.K, rule=u_bound_rule)

    def u_lower_rule(m, j, k):
        return m.u[j, k] >= 1
    model.u_lower = pyo.Constraint(model.C, model.K, rule=u_lower_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}