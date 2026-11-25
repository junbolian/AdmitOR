import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3]
    products = [0, 1]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    # Product-specific capacities
    prod_cap = {}
    prod_cap[(0, 1, 0)] = params["product_capacity_0_0to1"]
    prod_cap[(0, 1, 1)] = params["product_capacity_1_0to1"]
    prod_cap[(1, 0, 0)] = params["product_capacity_0_1to0"]
    prod_cap[(1, 0, 1)] = params["product_capacity_1_1to0"]

    generic_pairs = []
    for (i, j) in arcs:
        if (i, j) not in [(0, 1), (1, 0)]:
            generic_pairs.append((i, j))

    # For generic arcs, set product capacities using a deterministic rule within bounds
    # based on arc index, all reading from params.
    lo = params["product_capacity_generic_low"]
    hi = params["product_capacity_generic_high"]
    span = hi - lo

    for idx, (i, j) in enumerate(generic_pairs):
        # vary capacities within [lo, hi]
        for p in products:
            frac = ((idx * 2 + p) % 6) / 6.0
            prod_cap[(i, j, p)] = lo + frac * span

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=cities)
    model.P = pyo.Set(initialize=products)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    def x_bounds(m, i, j, p):
        return (0, prod_cap[(i, j, p)])
    model.x = pyo.Var(model.A, model.P, domain=pyo.NonNegativeReals, bounds=x_bounds)

    # Net demand: positive = demand (needs inflow), negative = supply (excess)
    net_demand = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): params["demand_city1_product0"],
        (1, 1): params["demand_city1_product1"],
        (2, 0): params["demand_city2_product0"],
        (2, 1): -params["supply_city2_product1"],
        (3, 0): -params["supply_city3_product0"],
        (3, 1): params["demand_city3_product1"],
    }

    # Flow balance: inflow - outflow = net_demand
    def flow_balance_rule(m, c, p):
        inflow = sum(m.x[i, c, p] for i in cities if i != c)
        outflow = sum(m.x[c, j, p] for j in cities if j != c)
        return inflow - outflow == net_demand[(c, p)]
    model.flow_balance = pyo.Constraint(model.C, model.P, rule=flow_balance_rule)

    # Joint capacity
    def joint_cap_rule(m, i, j):
        return sum(m.x[i, j, p] for p in products) <= params["joint_capacity"]
    model.joint_cap = pyo.Constraint(model.A, rule=joint_cap_rule)

    # Objective
    def obj_rule(m):
        return params["shipping_cost_per_unit"] * sum(m.x[i, j, p] for (i, j) in arcs for p in products)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}