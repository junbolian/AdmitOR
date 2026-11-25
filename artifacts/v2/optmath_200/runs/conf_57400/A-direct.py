import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2]
    products = [0, 1]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    # Net demand: positive = needs inflow, negative = excess outflow (supply)
    net = {
        (0, 0): params["net_demand_prod0_city0"],
        (0, 1): params["net_demand_prod0_city1"],
        (0, 2): -params["net_supply_prod0_city2"],
        (1, 0): -params["net_supply_prod1_city0"],
        (1, 1): params["net_demand_prod1_city1"],
        (1, 2): params["net_demand_prod1_city2"],
    }

    # Product-specific capacity per directed arc
    cap = {
        (0, 1, 0): params["prod_cap_01_p0"], (0, 1, 1): params["prod_cap_01_p1"],
        (0, 2, 0): params["prod_cap_02_p0"], (0, 2, 1): params["prod_cap_02_p1"],
        (1, 0, 0): params["prod_cap_10_p0"], (1, 0, 1): params["prod_cap_10_p1"],
        (1, 2, 0): params["prod_cap_12_p0"], (1, 2, 1): params["prod_cap_12_p1"],
        (2, 0, 0): params["prod_cap_20_p0"], (2, 0, 1): params["prod_cap_20_p1"],
        (2, 1, 0): params["prod_cap_21_p0"], (2, 1, 1): params["prod_cap_21_p1"],
    }

    shipping_cost = params["shipping_cost"]
    joint_capacity = params["joint_capacity"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.P, model.A, domain=pyo.NonNegativeReals)

    # Objective: minimize total shipping cost
    def obj_rule(m):
        return shipping_cost * sum(m.x[p, i, j] for p in m.P for (i, j) in m.A)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Flow balance: inflow - outflow = net demand
    def balance_rule(m, p, c):
        inflow = sum(m.x[p, i, c] for i in m.C if i != c)
        outflow = sum(m.x[p, c, j] for j in m.C if j != c)
        return inflow - outflow == net[(p, c)]
    model.balance = pyo.Constraint(model.P, model.C, rule=balance_rule)

    # Joint capacity across both products per city pair
    def joint_rule(m, i, j):
        return sum(m.x[p, i, j] for p in m.P) <= joint_capacity
    model.joint_cap = pyo.Constraint(model.A, rule=joint_rule)

    # Product-specific capacity
    def prod_rule(m, p, i, j):
        return m.x[p, i, j] <= cap[(i, j, p)]
    model.prod_cap = pyo.Constraint(model.P, model.A, rule=prod_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}