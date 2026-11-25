import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_trucks = int(params["num_trucks"])
    num_sites = int(params["num_sites"])
    cost = params["travel_cost"]

    # Nodes: 0 = base station, 1..num_sites = community sites
    num_nodes = num_sites + 1
    customers = list(range(1, num_nodes))
    vehicles = list(range(num_trucks))
    nodes = list(range(num_nodes))

    model = pyo.ConcreteModel()

    # Decision variables: x[k, i, j] = 1 if truck k travels edge i->j
    model.x = pyo.Var(vehicles, nodes, nodes, domain=pyo.Binary)

    # Objective: minimize total travel cost
    def obj_rule(m):
        return sum(
            cost[i][j] * m.x[k, i, j]
            for k in vehicles
            for i in nodes
            for j in nodes
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each customer visited exactly once (arrival)
    def visit_rule(m, j):
        return sum(m.x[k, i, j] for k in vehicles for i in nodes if i != j) == 1

    model.visit = pyo.Constraint(customers, rule=visit_rule)

    # Flow conservation for each truck at each node
    def flow_rule(m, k, j):
        out_flow = sum(m.x[k, j, i] for i in nodes if i != j)
        in_flow = sum(m.x[k, i, j] for i in nodes if i != j)
        return out_flow - in_flow == 0

    model.flow = pyo.Constraint(vehicles, nodes, rule=flow_rule)

    # Each truck departs from base at most once
    def depart_rule(m, k):
        return sum(m.x[k, 0, j] for j in customers) <= 1

    model.depart = pyo.Constraint(vehicles, rule=depart_rule)

    # Subtour elimination (MTZ) for each truck
    # u[k, i] = position/order of node i in truck k's route (for customers)
    model.u = pyo.Var(vehicles, customers, bounds=(1, num_sites))

    def mtz_rule(m, k, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return m.u[k, i] - m.u[k, j] + num_sites * m.x[k, i, j] <= num_sites - 1

    model.mtz = pyo.Constraint(vehicles, customers, customers, rule=mtz_rule)

    # Lower bound on u for customers only if visited by truck (each visited once overall)
    def u_lower_rule(m, k, i):
        return m.u[k, i] >= sum(m.x[k, p, i] for p in nodes if p != i)

    model.u_lower = pyo.Constraint(vehicles, customers, rule=u_lower_rule)

    # Solve with HiGHS
    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}