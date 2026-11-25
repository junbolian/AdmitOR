import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3]
    products = [0, 1]
    pairs = [(i, j) for i in cities for j in cities if i != j]

    net_supply = {
        (0, 0): params["net_supply_product0_city0"],
        (1, 0): params["net_supply_product1_city0"],
        (0, 1): params["net_supply_product0_city1"],
        (1, 1): params["net_supply_product1_city1"],
        (0, 2): params["net_supply_product0_city2"],
        (1, 2): params["net_supply_product1_city2"],
        (0, 3): params["net_supply_product0_city3"],
        (1, 3): params["net_supply_product1_city3"],
    }

    capacity_pc = {
        (0, 0, 1): params["capacity_product0_city0_city1"],
        (1, 0, 1): params["capacity_product1_city0_city1"],
        (0, 2, 3): params["capacity_product0_city2_city3"],
        (1, 2, 3): params["capacity_product1_city2_city3"],
    }

    cost = params["transport_cost_per_unit"]
    total_cap = params["total_shipping_capacity_any_pair"]

    model = pyo.ConcreteModel()

    model.product = pyo.Set(initialize=products)
    model.city = pyo.Set(initialize=cities)
    model.arc = pyo.Set(initialize=pairs, dimen=2)

    model.ship = pyo.Var(model.product, model.arc, domain=pyo.NonNegativeReals)

    def objective_rule(m):
        return sum(
            cost * m.ship[p, (i, j)]
            for p in m.product
            for (i, j) in m.arc
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def flow_balance_rule(m, p, c):
        return net_supply[(p, c)] + inflow(p, c, m) - outflow(p, c, m) == 0

    def inflow(p, c, m):
        return sum(m.ship[p, (i, c)] for i in cities if i != c)

    def outflow(p, c, m):
        return sum(m.ship[p, (c, j)] for j in cities if j != c)

    model.flow_balance = pyo.Constraint(model.product, model.city, rule=flow_balance_rule)

    def total_capacity_rule(m, i, j):
        return (
            sum(m.ship[p, (i, j)] for p in m.product)
            + sum(m.ship[p, (j, i)] for p in m.product)
            <= total_cap
        )

    model.total_capacity = pyo.Constraint(model.arc, rule=total_capacity_rule)

    def product_capacity_rule(m, p, i, j):
        if i > j:
            return pyo.Constraint.Skip
        key = (p, i, j)
        if key in capacity_pc:
            return m.ship[p, (i, j)] + m.ship[p, (j, i)] <= capacity_pc[key]
        return pyo.Constraint.Skip

    model.product_capacity = pyo.Constraint(
        model.product, model.arc, rule=product_capacity_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}