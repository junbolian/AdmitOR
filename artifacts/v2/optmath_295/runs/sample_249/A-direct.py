import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3]
    products = [0, 1]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.products = pyo.Set(initialize=products)
    model.cities = pyo.Set(initialize=cities)

    model.flow = pyo.Var(model.products, model.arcs, bounds=lambda m, p, i, j: (
        0,
        params["product{p}_capacity_{i}{j}".format(p=p, i=i, j=j)],
    ))

    def obj_rule(m):
        return params["transport_cost"] * sum(
            m.flow[p, i, j] for p in m.products for (i, j) in m.arcs
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, c, p):
        outflow = sum(m.flow[p, c, j] for j in m.cities if j != c)
        inflow = sum(m.flow[p, i, c] for i in m.cities if i != c)
        return outflow - inflow == params["net_flow_{c}_product{p}".format(c=c, p=p)]

    model.balance = pyo.Constraint(model.cities, model.products, rule=balance_rule)

    def joint_rule(m, i, j):
        return sum(m.flow[p, i, j] for p in m.products) <= params["joint_capacity"]

    model.joint_cap = pyo.Constraint(model.arcs, rule=joint_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}