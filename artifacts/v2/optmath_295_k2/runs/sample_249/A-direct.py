import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3]
    products = [0, 1]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def bal(p, i):
        return params[f"net_flow_city{i}_product{p}"]

    def pcap(p, i, j):
        return params[f"product{p}_capacity_city{i}_city{j}"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(dimen=2, initialize=arcs)

    model.x = pyo.Var(model.P, model.A, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(params["transport_cost_per_unit"] * m.x[p, i, j] for p in m.P for (i, j) in m.A)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def product_cap_rule(m, p, i, j):
        return m.x[p, i, j] <= pcap(p, i, j)
    model.product_cap = pyo.Constraint(model.P, model.A, rule=product_cap_rule)

    def joint_cap_rule(m, i, j):
        return sum(m.x[p, i, j] for p in m.P) <= params["joint_capacity_per_pair"]
    model.joint_cap = pyo.Constraint(model.A, rule=joint_cap_rule)

    def balance_rule(m, p, i):
        outflow = sum(m.x[p, i, j] for j in m.C if j != i)
        inflow = sum(m.x[p, j, i] for j in m.C if j != i)
        return outflow - inflow == bal(p, i)
    model.balance = pyo.Constraint(model.P, model.C, rule=balance_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}