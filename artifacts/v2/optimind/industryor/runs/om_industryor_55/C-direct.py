import gurobipy as gp
from gurobipy import GRB
from itertools import product

def solve(params):
    order_widths = params["order_widths"]   # list of widths per order
    order_lengths = params["order_lengths"] # list of lengths per order
    stock_widths = params["stock_widths"]   # list of standard roll widths

    n_orders = len(order_widths)
    n_stocks = len(stock_widths)

    # Generate all feasible cutting patterns for each stock width.
    # A pattern is a tuple (a_1, a_2, ..., a_n) where a_i is the number of
    # times order i's width is cut from one roll of this stock width.
    # Constraint: sum(a_i * order_widths[i]) <= stock_widths[s]

    patterns = []        # list of (stock_index, [a_1,...,a_n])
    pattern_stock = []   # which stock width each pattern belongs to

    def enumerate_patterns(stock_w, order_ws):
        """Return all non-negative integer combinations that fit in stock_w."""
        results = []
        max_cuts = [int(stock_w / order_ws[i]) for i in range(len(order_ws))]

        ranges = [range(0, max_cuts[i] + 1) for i in range(len(order_ws))]
        for combo in product(*ranges):
            used = sum(combo[i] * order_ws[i] for i in range(len(order_ws)))
            if used <= stock_w + 1e-9:
                results.append(list(combo))
        return results

    for s in range(n_stocks):
        pats = enumerate_patterns(stock_widths[s], order_widths)
        for pat in pats:
            patterns.append(pat)
            pattern_stock.append(s)

    n_patterns = len(patterns)

    # Decision variable x[p] = length (meters) of stock roll cut using pattern p.
    # The length of stock consumed by pattern p is x[p] (since width is fixed by
    # the stock, length is the continuous dimension we allocate).
    #
    # For each order i, the total length produced is:
    #   sum_p  patterns[p][i] * x[p]  >= order_lengths[i]
    #
    # Waste area = total stock area used - total order area required
    # Total stock area used = sum_p  stock_widths[pattern_stock[p]] * x[p]
    # Total order area      = sum_i  order_widths[i] * order_lengths[i]  (fixed)
    #
    # Minimising waste area is equivalent to minimising total stock area used.

    model = gp.Model("paper_cutting")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_patterns, lb=0.0, name="x")

    # Objective: minimise total stock area consumed
    model.setObjective(
        gp.quicksum(
            stock_widths[pattern_stock[p]] * x[p]
            for p in range(n_patterns)
        ),
        GRB.MINIMIZE
    )

    # Demand constraints: each order's length requirement must be met
    for i in range(n_orders):
        model.addConstr(
            gp.quicksum(patterns[p][i] * x[p] for p in range(n_patterns))
            >= order_lengths[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        total_stock_area = model.ObjVal
        total_order_area = sum(order_widths[i] * order_lengths[i] for i in range(n_orders))
        waste_area = total_stock_area - total_order_area
        return {"objective": waste_area, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}