import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_capacity = params["machine_capacity"]
    machine_time_req = params["machine_time_req"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]
    borer_downtime_period = params["borer_downtime_period"]

    products = ["product_0", "product_1", "product_2", "product_3"]
    periods = list(range(6))
    machines = ["grinder", "drill", "borer"]

    # Normalize machine_capacity to a dict keyed by machine name
    if isinstance(machine_capacity, dict):
        cap_dict = machine_capacity
    else:
        cap_dict = {m: machine_capacity[i] for i, m in enumerate(machines)}

    # Normalize machine_time_req to dict[machine][product] = hours
    time_req = {}
    for i, m in enumerate(machines):
        if isinstance(machine_time_req, dict):
            entry = machine_time_req[m]
        else:
            entry = machine_time_req[i]
        if isinstance(entry, dict):
            time_req[m] = entry
        else:
            time_req[m] = {p: entry[j] for j, p in enumerate(products)}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    # Balance constraints
    def balance_rule(model, p, t):
        prev = 0
        if t > 0:
            prev = model.inventory[p, t - 1]
        return prev + model.produce[p, t] == model.sell[p, t] + model.inventory[p, t]

    model.balance_con = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Machine capacity constraints
    def capacity_rule(model, mk, t):
        cap = cap_dict[mk]
        if mk == "borer" and t == borer_downtime_period:
            cap = 0
        return sum(time_req[mk][p] * model.produce[p, t] for p in model.P) <= cap

    model.capacity_con = pyo.Constraint(model.M, model.T, rule=capacity_rule)

    # Inventory limit
    def inv_limit_rule(model, p, t):
        return model.inventory[p, t] <= inventory_limit

    model.inv_limit_con = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    # Sales limit
    def sales_limit_rule(model, p, t):
        idx_p = products.index(p)
        return model.sell[p, t] <= sales_limit[idx_p][t]

    model.sales_limit_con = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    # Target inventory
    def target_rule(model, p):
        return model.inventory[p, periods[-1]] == target_inventory[products.index(p)]

    model.target_con = pyo.Constraint(model.P, rule=target_rule)

    # Objective
    def obj_rule(model):
        revenue = sum(
            profit_per_unit[products.index(p)] * model.sell[p, t]
            for p in model.P for t in model.T
        )
        holding = sum(
            holding_cost * model.inventory[p, t]
            for p in model.P for t in model.T
        )
        return revenue - holding

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}