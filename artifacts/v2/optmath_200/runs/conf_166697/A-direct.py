import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants
    products = [0, 1]
    periods = [0, 1, 2]
    T = len(periods)

    # Read all numeric quantities from params
    setup_cost = params["setup_cost"]
    startup_cost = params["startup_cost"]
    capacity = params["capacity"]
    startup_time = params["startup_time"]
    holding_cost = {0: params["holding_cost_P0"], 1: params["holding_cost_P1"]}
    backlog_cost = {0: params["backlog_cost_P0"], 1: params["backlog_cost_P1"]}
    demand = {}
    for i in products:
        for t in periods:
            demand[(i, t)] = params[f"demand_P{i}_P{t}"]

    model = pyo.ConcreteModel()

    # Sets
    model.products = pyo.Set(initialize=products)
    model.periods = pyo.Set(initialize=periods)

    # Decision variables
    # Setup: whether product i is produced in period t
    model.setup = pyo.Var(model.products, model.periods, domain=pyo.Binary)
    # Startup: whether machine is started for product i in period t
    model.startup = pyo.Var(model.products, model.periods, domain=pyo.Binary)
    # Production quantity
    model.prod = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)
    # Inventory
    model.inv = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)
    # Backlog
    model.backlog = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)

    # Objective
    def obj_rule(model_expr):
        total = 0.0
        for i in products:
            for t in periods:
                total = total + setup_cost * model_expr.setup[i, t]
                total = total + startup_cost * model_expr.startup[i, t]
                total = total + holding_cost[i] * model_expr.inv[i, t]
                total = total + backlog_cost[i] * model_expr.backlog[i, t]
        return total

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Inventory balance constraints
    # inv[i,t-1] - backlog[i,t-1] + prod[i,t] + backlog[i,t] - inv[i,t] = demand[i,t]
    def balance_rule(model_expr, i, t):
        if t == 0:
            prev_inv = 0.0
            prev_backlog = 0.0
        else:
            prev_inv = model_expr.inv[i, t - 1]
            prev_backlog = model_expr.backlog[i, t - 1]
        return (prev_inv - prev_backlog + model_expr.prod[i, t]
                + model_expr.backlog[i, t] - model_expr.inv[i, t]) == demand[(i, t)]

    model.balance = pyo.Constraint(model.products, model.periods, rule=balance_rule)

    # Capacity constraints: sum of production + startup_time * startup <= capacity
    def cap_rule(model_expr, t):
        total_prod = 0.0
        total_startup = 0.0
        for i in products:
            total_prod = total_prod + model_expr.prod[i, t]
            total_startup = total_startup + model_expr.startup[i, t]
        return total_prod + startup_time * total_startup <= capacity

    model.cap = pyo.Constraint(model.periods, rule=cap_rule)

    # Only one product can be produced (set up) per period
    def one_prod_rule(model_expr, t):
        total = 0.0
        for i in products:
            total = total + model_expr.setup[i, t]
        return total <= 1

    model.one_prod = pyo.Constraint(model.periods, rule=one_prod_rule)

    # Production only if setup is active
    def setup_link_rule(model_expr, i, t):
        return model_expr.prod[i, t] <= capacity * model_expr.setup[i, t]

    model.setup_link = pyo.Constraint(model.products, model.periods, rule=setup_link_rule)

    # Startup linking: startup[i,t] >= setup[i,t] - setup[i,t-1] (with setup[i,-1]=0)
    def startup_link_rule(model_expr, i, t):
        if t == 0:
            prev = 0.0
        else:
            prev = model_expr.setup[i, t - 1]
        return model_expr.startup[i, t] >= model_expr.setup[i, t] - prev

    model.startup_link = pyo.Constraint(model.products, model.periods, rule=startup_link_rule)

    # Startup implies setup
    def startup_implies_setup_rule(model_expr, i, t):
        return model_expr.startup[i, t] <= model_expr.setup[i, t]

    model.startup_implies_setup = pyo.Constraint(model.products, model.periods,
                                                  rule=startup_implies_setup_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}