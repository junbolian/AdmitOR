import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_customers = int(params["num_customers"])
    num_vehicles = int(params["num_vehicles"])

    nodes = list(range(num_nodes))
    customers = list(range(1, num_nodes))
    vehicles = list(range(num_vehicles))

    dist = {}
    for i in nodes:
        for j in nodes:
            dist[(i, j)] = params["distance_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, nodes, vehicles, domain=pyo.Binary)

    def obj_rule(md):
        return sum(dist[(i, j)] * md.x[i, j, k]
                   for i in nodes for j in nodes for k in vehicles)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_degree_rule(md, j):
        return sum(md.x[i, j, k] for i in nodes for k in vehicles if i != j) == 1
    model.out_degree = pyo.Constraint(customers, rule=out_degree_rule)

    def in_degree_rule(md, i):
        return sum(md.x[i, j, k] for j in nodes for k in vehicles if i != j) == 1
    model.in_degree = pyo.Constraint(customers, rule=in_degree_rule)

    def depot_out_rule(md, k):
        return sum(md.x[0, j, k] for j in customers) == 1
    model.depot_out = pyo.Constraint(vehicles, rule=depot_out_rule)

    def depot_in_rule(md, k):
        return sum(md.x[i, 0, k] for i in customers) == 1
    model.depot_in = pyo.Constraint(vehicles, rule=depot_in_rule)

    for k in vehicles:
        model.x[0, 0, k].fix(0)

    model.u = pyo.Var(customers, bounds=(0, num_customers))

    def subtour_rule(md, i, j):
        if i == j:
            return pyo.Constraint.Skip
        inner = sum(md.x[i, j, k] for k in vehicles)
        return md.u[i] - md.u[j] + num_customers * inner <= num_customers - 1
    model.subtour = pyo.Constraint(customers, customers, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}