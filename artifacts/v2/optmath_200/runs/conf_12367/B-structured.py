# IR: {"sets":{"products":[0,1],"cities":[0,1,2,3],"arcs":"(i,j): i != j","pairs":"(i,j): i < j","limited_pairs":[[0,1],[2,3]]},"params":{"transport_cost_per_unit":"scalar","net_supply_product0_city0":"scalar","net_supply_product1_city0":"scalar","net_supply_product0_city1":"scalar","net_supply_product1_city1":"scalar","net_supply_product0_city2":"scalar","net_supply_product1_city2":"scalar","net_supply_product0_city3":"scalar","net_supply_product1_city3":"scalar","total_shipping_capacity_any_pair":"scalar","capacity_product0_city0_city1":"scalar","capacity_product1_city0_city1":"scalar","capacity_product0_city2_city3":"scalar","capacity_product1_city2_city3":"scalar"},"variables":{"shipment[p,i,j]":"nonnegative continuous"},"constraints":["For each product p and city i: sum_{j != i} shipment[p,i,j] - sum_{j != i} shipment[p,j,i] <= net_supply_product{p}_city{i}; positive supply is availability, negative supply is required demand, and surplus may remain unused.","For each unordered pair (i,j): sum_p (shipment[p,i,j] + shipment[p,j,i]) <= total_shipping_capacity_any_pair.","For each product p and limited pair (i,j): shipment[p,i,j] + shipment[p,j,i] <= capacity_product{p}_city{i}_city{j}."],"objective":"Minimize transport_cost_per_unit * sum_{p,(i,j) in arcs} shipment[p,i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = (0, 1)
    cities = (0, 1, 2, 3)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    pairs = [(i, j) for i in cities for j in cities if i < j]
    limited_pairs = [(0, 1), (2, 3)]

    transport_cost = params["transport_cost_per_unit"]
    total_capacity = params["total_shipping_capacity_any_pair"]

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
    product_capacity = {
        (0, 0, 1): params["capacity_product0_city0_city1"],
        (1, 0, 1): params["capacity_product1_city0_city1"],
        (0, 2, 3): params["capacity_product0_city2_city3"],
        (1, 2, 3): params["capacity_product1_city2_city3"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products)
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.pairs = pyo.Set(dimen=2, initialize=pairs)
    model.limited_pairs = pyo.Set(dimen=2, initialize=limited_pairs)

    model.shipment = pyo.Var(
        model.products, model.arcs, domain=pyo.NonNegativeReals
    )

    # Supply is available stock, not a requirement to ship surplus stock.
    # This permits excess supply while requiring all negative net supplies
    # (demands) to be satisfied.
    def balance_rule(instance, product, city):
        outgoing = sum(
            instance.shipment[product, city, other]
            for other in cities
            if other != city
        )
        incoming = sum(
            instance.shipment[product, other, city]
            for other in cities
            if other != city
        )
        return outgoing - incoming <= net_supply[product, city]

    model.flow_balance = pyo.Constraint(
        model.products, model.cities, rule=balance_rule
    )

    def pair_capacity_rule(instance, i, j):
        return sum(
            instance.shipment[product, i, j]
            + instance.shipment[product, j, i]
            for product in products
        ) <= total_capacity

    model.shared_capacity = pyo.Constraint(
        model.pairs, rule=pair_capacity_rule
    )

    def product_capacity_rule(instance, product, i, j):
        return (
            instance.shipment[product, i, j]
            + instance.shipment[product, j, i]
            <= product_capacity[product, i, j]
        )

    model.product_pair_capacity = pyo.Constraint(
        model.products, model.limited_pairs, rule=product_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=transport_cost
        * sum(
            model.shipment[product, i, j]
            for product in products
            for i, j in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}