# panel_base_2of3 certificates that miss the OptiMind answer and are not panel_base_3of3 certificates

Every panel_base_2of3 certificate whose value misses the answer on a problem without a panel_base_3of3 certificate. OptiMind cleaned IndustryOR and Mamo-Complex (`datasets/optimind_corrected/SOURCE.md`), scored with `round_aware` of scripts/score_eval.py against the OptiMind answers. Sections: identification, problem text, extracted parameter set with warnings, the three programs, values on the stated and resampled instances (both samplers), and the data-verification replies of the three families.

| Sample id | Benchmark | Problem class | Certified value | Answer | B or C flags |
|---|---|---|---:|---:|---|
| `om_industryor_5` | OptiMind IndustryOR | ['Capacitated Lot-sizing Problem (CLSP)'] | 10750.0 | 10755 | no |
| `om_industryor_10` | OptiMind IndustryOR | ['Production Planning Problem', 'Operations Optimization'] | 194.66666666666669 | 272 | no |
| `om_industryor_14` | OptiMind IndustryOR | ['Lot-Sizing Problem'] | 141.0 | 134 | no |
| `om_industryor_23` | OptiMind IndustryOR | ['PortfolioOptimization'] | 140000.0 | 510000 | yes |
| `om_industryor_25` | OptiMind IndustryOR | ['Factory Planning Problem', 'Production Planning Problem'] | 1146.5665024630541 | 1146.4142 | no |
| `om_industryor_43` | OptiMind IndustryOR | ['Production Planning Problem', 'Profit Maximization Problem'] | 715.0 | 712 | no |
| `om_industryor_69` | OptiMind IndustryOR | ['Assignment Problem'] | 340.0 | 330 | yes |
| `om_industryor_92` | OptiMind IndustryOR | ['Blending Problem'] | 8000000.0 | 5000000 | no |
| `om_mamo_2` | OptiMind Mamo-Complex | ["Network Optimization"] | 109.0 | 43 | yes |
| `om_mamo_125` | OptiMind Mamo-Complex | ["Network Optimization"] | 59.0 | 46 | yes |
| `om_mamo_173` | OptiMind Mamo-Complex | ['Transportation Problem'] | 0.0 | 7084 | yes |
| `om_mamo_182` | OptiMind Mamo-Complex | ['Diet Problem'] | 15.235121951219512 | 17 | no |
| `om_mamo_183` | OptiMind Mamo-Complex | ["Blending Problem"] | 21.606250000000003 | 0.2160625 | no |
| `om_mamo_205` | OptiMind Mamo-Complex | ["Network Optimization"] | 68000.0 | 70000 | yes |

## 1. om_industryor_5 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_5` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 5) |
| Problem class (OptiMind) | ['Capacitated Lot-sizing Problem (CLSP)'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 10750.0 |
| Answer (OptiMind) | 10755 |
| Rules that certify it | gate 10750.0, panel_base_2of3 10750.0, ind_gate 10750.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
The contract reservations for the next year for products I, II, and III of a certain factory in each quarter are shown in Table 1-10.

Table 1-10
| Product | 1    | 2    | 3    | 4    |
|---------|------|------|------|------|
| I       | 1500 | 1000 | 2000 | 1200 |
| II      | 1500 | 1500 | 1200 | 1500 |
| III     | 1000 | 2000 | 1500 | 2500 |

At the beginning of the first quarter, there is no inventory for these three products, and it is required to have 150 units in stock for each product by the end of the fourth quarter. It is known that the factory has 15,000 production hours per quarter, and each unit of products I, II, and III requires 2, 4, and 3 hours respectively. Due to a change in equipment, product I cannot be produced in the second quarter. It is stipulated that if the products cannot be delivered on time, a compensation of 20 yuan per unit per quarter delay is required for products I and II, while for product III, the compensation is 10 yuan. Additionally, for products produced but not delivered in the current quarter, the inventory cost is 5 yuan per unit per quarter. How should the factory schedule production to minimize the total cost of compensation and inventory?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"reservations": {"base":[[1500,1000,2000,1200],[1500,1500,1200,1500],[1000,2000,1500,2500]],"perturb":{"mode":"rel","r":0.3}}
"ending_inventory_required": {"base":150,"perturb":{"mode":"abs","lo":0.0,"hi":400.0,"integer":true}}
"production_hours_per_quarter": {"base":15000,"perturb":{"mode":"rel","r":0.25}}
"hours_per_unit": {"base":[2,4,3],"perturb":{"mode":"rel","r":0.3}}
"delay_penalty": {"base":[20,20,10],"perturb":{"mode":"rel","r":0.5}}
"inventory_cost": {"base":5,"perturb":{"mode":"abs","lo":1.0,"hi":20.0,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    reservations = params["reservations"]
    ending_inventory_required = params["ending_inventory_required"]
    production_hours_per_quarter = params["production_hours_per_quarter"]
    hours_per_unit = params["hours_per_unit"]
    delay_penalty = params["delay_penalty"]
    inventory_cost = params["inventory_cost"]

    products = [0, 1, 2]
    quarters = [0, 1, 2, 3]
    forbidden = {(0, 1)}

    demand = {(i, t): reservations[i][t] for i in products for t in quarters}
    hpu = {i: hours_per_unit[i] for i in products}
    delay_cost = {i: delay_penalty[i] for i in products}
    end_req = {i: ending_inventory_required[i] for i in products}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.short = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.delivered = pyo.Var(products, quarters, within=pyo.NonNegativeReals)

    for (i, t) in forbidden:
        model.x[i, t].fix(0)

    model.cap = pyo.Constraint(
        quarters,
        rule=lambda m, t: sum(hpu[i] * m.x[i, t] for i in products)
        <= production_hours_per_quarter,
    )

    def inv_flow(m, i, t):
        prev_inv = 0 if t == 0 else m.inv[i, t - 1]
        return m.inv[i, t] == m.x[i, t] + prev_inv - m.delivered[i, t]

    model.inv_flow = pyo.Constraint(products, quarters, rule=inv_flow)

    model.deliver_def = pyo.Constraint(
        products,
        quarters,
        rule=lambda m, i, t: m.delivered[i, t] + m.short[i, t] == demand[i, t],
    )

    def deliver_limit(m, i, t):
        prev_inv = 0 if t == 0 else m.inv[i, t - 1]
        return m.delivered[i, t] <= m.x[i, t] + prev_inv

    model.deliver_limit = pyo.Constraint(products, quarters, rule=deliver_limit)

    model.endstock = pyo.Constraint(
        products, rule=lambda m, i: m.inv[i, 3] >= end_req[i]
    )

    model.obj = pyo.Objective(
        expr=sum(delay_cost[i] * model.short[i, t] for i in products for t in quarters)
        + sum(inventory_cost * model.inv[i, t] for i in products for t in quarters),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"P":[0,1,2],"Q":[0,1,2,3]},"params":["reservations","ending_inventory_required","production_hours_per_quarter","hours_per_unit","delay_penalty","inventory_cost"],"variables":{"production[P,Q]":"NonNegativeReals","inventory[P,Q]":"NonNegativeReals","backlog[P,Q]":"NonNegativeReals"},"constraints":["For each product and quarter: previous_inventory - previous_backlog + production - reservations = inventory - backlog; initial inventory and backlog are zero.","For each quarter: sum(hours_per_unit[p] * production[p,q] for p in P) <= production_hours_per_quarter.","production[0,1] = 0.","For each product: inventory[p,3] >= ending_inventory_required.","For each product: backlog[p,3] = 0."],"objective":"Minimize sum(inventory_cost * inventory[p,q] + delay_penalty[p] * backlog[p,q] for p in P, q in Q)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    reservations = params["reservations"]
    ending_inventory_required = params["ending_inventory_required"]
    production_hours_per_quarter = params["production_hours_per_quarter"]
    hours_per_unit = params["hours_per_unit"]
    delay_penalty = params["delay_penalty"]
    inventory_cost = params["inventory_cost"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 2)
    model.quarters = pyo.RangeSet(0, 3)

    model.production = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.backlog = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, product, quarter):
        previous_inventory = (
            0 if quarter == 0 else instance.inventory[product, quarter - 1]
        )
        previous_backlog = (
            0 if quarter == 0 else instance.backlog[product, quarter - 1]
        )
        return (
            previous_inventory
            - previous_backlog
            + instance.production[product, quarter]
            - reservations[product][quarter]
            == instance.inventory[product, quarter]
            - instance.backlog[product, quarter]
        )

    model.material_balance = pyo.Constraint(
        model.products, model.quarters, rule=balance_rule
    )

    def capacity_rule(instance, quarter):
        return sum(
            hours_per_unit[product] * instance.production[product, quarter]
            for product in instance.products
        ) <= production_hours_per_quarter

    model.quarterly_capacity = pyo.Constraint(
        model.quarters, rule=capacity_rule
    )

    model.product_one_shutdown = pyo.Constraint(
        expr=model.production[0, 1] == 0
    )

    def ending_inventory_rule(instance, product):
        return instance.inventory[product, 3] >= ending_inventory_required

    model.required_ending_inventory = pyo.Constraint(
        model.products, rule=ending_inventory_rule
    )

    def final_backlog_rule(instance, product):
        return instance.backlog[product, 3] == 0

    model.final_delivery_completion = pyo.Constraint(
        model.products, rule=final_backlog_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            inventory_cost * model.inventory[product, quarter]
            + delay_penalty[product] * model.backlog[product, quarter]
            for product in model.products
            for quarter in model.quarters
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Success is still determined solely by objective retrieval below.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    reservations = params["reservations"]                    # shape (3, 4)
    ending_inv_req = params["ending_inventory_required"]     # scalar or length-3 list
    prod_hours_per_q = params["production_hours_per_quarter"]  # scalar
    hours_per_unit = params["hours_per_unit"]                # length 3
    delay_penalty = params["delay_penalty"]                  # length 3
    inventory_cost = params["inventory_cost"]                # scalar or length 3

    I = 3   # products: 0=I, 1=II, 2=III
    Q = 4   # quarters: 0..3

    # Normalize ending_inv_req to a list of length I
    if hasattr(ending_inv_req, '__len__'):
        end_req = [ending_inv_req[i] for i in range(I)]
    else:
        end_req = [ending_inv_req] * I

    # Normalize inventory_cost to a list of length I
    if hasattr(inventory_cost, '__len__'):
        inv_cost = [inventory_cost[i] for i in range(I)]
    else:
        inv_cost = [inventory_cost] * I

    model = gp.Model("production_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i, q] = units of product i produced in quarter q
    x = model.addVars(I, Q, lb=0.0, name="x")

    # Product I (index 0) cannot be produced in quarter 2 (index 1)
    model.addConstr(x[0, 1] == 0, name="no_prod_I_Q2")

    # Production hours constraint per quarter
    for q in range(Q):
        model.addConstr(
            gp.quicksum(hours_per_unit[i] * x[i, q] for i in range(I)) <= prod_hours_per_q,
            name=f"hours_q{q}"
        )

    # inv[i,q]: finished goods inventory at end of quarter q (produced but undelivered)
    # back[i,q]: backlog (unmet demand) at end of quarter q
    # Net stock balance: inv[i,q] - back[i,q] = inv[i,q-1] - back[i,q-1] + x[i,q] - demand[i,q]
    # The optimizer naturally avoids simultaneous positive inv and back due to cost penalties.

    inv = model.addVars(I, Q, lb=0.0, name="inv")
    back = model.addVars(I, Q, lb=0.0, name="back")

    for i in range(I):
        for q in range(Q):
            dem = reservations[i][q]
            if q == 0:
                prev_inv = 0.0
                prev_back = 0.0
            else:
                prev_inv = inv[i, q - 1]
                prev_back = back[i, q - 1]
            model.addConstr(
                inv[i, q] - back[i, q] == prev_inv - prev_back + x[i, q] - dem,
                name=f"balance_i{i}_q{q}"
            )

    # Ending inventory requirement: inventory at end of Q4 >= required, no backlog
    for i in range(I):
        model.addConstr(inv[i, Q - 1] >= end_req[i], name=f"end_inv_i{i}")
        model.addConstr(back[i, Q - 1] == 0, name=f"end_back_i{i}")

    # Objective: inventory holding cost + delay penalty cost
    # Each unit of inventory held for a quarter costs inv_cost[i].
    # Each unit of backlog held for a quarter costs delay_penalty[i] (1 quarter of delay).
    obj = gp.quicksum(
        inv_cost[i] * inv[i, q] + delay_penalty[i] * back[i, q]
        for i in range(I)
        for q in range(Q)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 10750.0 (optimal) | 10750.0 (optimal) |
| 1 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 3880.935601698895 (optimal) | 3880.9356016988954 (optimal) |
| 2 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 78479.53814388918 (optimal) | 78479.5381438892 (optimal) |
| 3 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 9248.290102851895 (optimal) | 9248.290102851894 (optimal) |
| 4 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 5212.035015765304 (optimal) | 5212.035015765305 (optimal) |
| 5 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 19217.969781157593 (optimal) | 19217.969781157593 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 10750.0 (optimal) | 10750.0 (optimal) |
| 1 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | none (solver_failed) | none (infeasible) |
| 2 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | none (solver_failed) | none (infeasible) |
| 3 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 23796.867512658326 (optimal) | 23796.86751265832 (optimal) |
| 4 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 30333.290246106313 (optimal) | 30333.29024610631 (optimal) |
| 5 | none (crash:end_req = {i: ending_inventory_required[i] for i in products} \| ~~~~~~~~~~~~~~~~~~~~~~~~~^^^ \| TypeError: 'int' object is not subscriptable) | 21258.177592532684 (optimal) | 21258.177592532684 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 2. om_industryor_10 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_10` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 10) |
| Problem class (OptiMind) | ['Production Planning Problem', 'Operations Optimization'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 194.66666666666669 |
| Answer (OptiMind) | 272 |
| Rules that certify it | panel_base_2of3 194.66666666666669 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A company produces two types of small motorcycles, where type A is entirely manufactured by the company, and type B is assembled from imported parts. The production, assembly, and inspection time required for each unit of these two products are shown in Table 3.2.

Table 3.2

| Type | Process | | | Selling Price <br> (Yuan/unit) |
| :---: | :---: | :---: | :---: | :---: |
| | Manufacturing | Assembly | Inspection | |
| Type A (hours/unit) | 20 | 5 | 3 | 650 |
| Type B (hours/unit) | 0 | 7 | 6 | 725 |
| Max production capacity per week (hours) | 120 | 80 | 40 | |
| Production cost per hour (Yuan) | 12 | 8 | 10 | |

If the company's operational goals and targets are as follows:

$p_{1}$ : The total profit per week should be at least 3000 yuan;

$p_{2}$ : At least 5 units of type A motorcycles should be produced per week;

$p_{3}$ : Minimize the idle time of each process as much as possible. The weight coefficients of the three processes are their hourly costs, and overtime is not allowed.

Try to establish a model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"price_A": {"base":650,"perturb":{"mode":"rel","r":0.2}}
"price_B": {"base":725,"perturb":{"mode":"rel","r":0.2}}
"hours_manuf_A": {"base":20,"perturb":{"mode":"rel","r":0.2}}
"hours_asm_A": {"base":5,"perturb":{"mode":"rel","r":0.2}}
"hours_insp_A": {"base":3,"perturb":{"mode":"rel","r":0.2}}
"hours_manuf_B": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":5.0,"integer":false}}
"hours_asm_B": {"base":7,"perturb":{"mode":"rel","r":0.2}}
"hours_insp_B": {"base":6,"perturb":{"mode":"rel","r":0.2}}
"cap_manuf": {"base":120,"perturb":{"mode":"rel","r":0.25}}
"cap_asm": {"base":80,"perturb":{"mode":"rel","r":0.25}}
"cap_insp": {"base":40,"perturb":{"mode":"rel","r":0.25}}
"cost_manuf": {"base":12,"perturb":{"mode":"rel","r":0.25}}
"cost_asm": {"base":8,"perturb":{"mode":"rel","r":0.25}}
"cost_insp": {"base":10,"perturb":{"mode":"rel","r":0.25}}
"profit_target": {"base":3000,"perturb":{"mode":"rel","r":0.3}}
"min_A_target": {"base":5,"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price_A = params["price_A"]
    price_B = params["price_B"]

    hours_manuf_A = params["hours_manuf_A"]
    hours_asm_A = params["hours_asm_A"]
    hours_insp_A = params["hours_insp_A"]
    hours_manuf_B = params["hours_manuf_B"]
    hours_asm_B = params["hours_asm_B"]
    hours_insp_B = params["hours_insp_B"]

    cap_manuf = params["cap_manuf"]
    cap_asm = params["cap_asm"]
    cap_insp = params["cap_insp"]

    cost_manuf = params["cost_manuf"]
    cost_asm = params["cost_asm"]
    cost_insp = params["cost_insp"]

    profit_target = params["profit_target"]
    min_A_target = params["min_A_target"]

    model = pyo.ConcreteModel()

    # Decision variables: production quantities
    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    # Goal deviation variables (under/over achievements)
    # p1: profit >= profit_target -> minimize under-achievement d1_minus
    model.d1_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d1_plus = pyo.Var(domain=pyo.NonNegativeReals)
    # p2: xA >= min_A_target -> minimize under-achievement d2_minus
    model.d2_minus = pyo.Var(domain=pyo.NonNegativeReals)
    model.d2_plus = pyo.Var(domain=pyo.NonNegativeReals)

    # Idle time slack variables for each process (idle = capacity - used)
    model.idle_manuf = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle_asm = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle_insp = pyo.Var(domain=pyo.NonNegativeReals)

    # Objective weights: lexicographic via large weights for p1, p2, then idle costs
    W1 = 1e6
    W2 = 1e5
    W3 = 1.0

    def obj_rule(m):
        return (
            W1 * m.d1_minus
            + W2 * m.d2_minus
            + W3 * (cost_manuf * m.idle_manuf + cost_asm * m.idle_asm + cost_insp * m.idle_insp)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Profit goal constraint: profit + d1_minus - d1_plus = profit_target
    # Profit = revenue - cost = price_A*xA + price_B*xB - (cost per hour * hours used)
    def profit_rule(m):
        revenue = price_A * m.xA + price_B * m.xB
        cost = (
            cost_manuf * (hours_manuf_A * m.xA + hours_manuf_B * m.xB)
            + cost_asm * (hours_asm_A * m.xA + hours_asm_B * m.xB)
            + cost_insp * (hours_insp_A * m.xA + hours_insp_B * m.xB)
        )
        return revenue - cost + m.d1_minus - m.d1_plus == profit_target

    model.profit_goal = pyo.Constraint(rule=profit_rule)

    # Min A production goal: xA + d2_minus - d2_plus = min_A_target
    def min_A_rule(m):
        return m.xA + m.d2_minus - m.d2_plus == min_A_target

    model.min_A_goal = pyo.Constraint(rule=min_A_rule)

    # Capacity (no overtime) constraints with idle time
    def manuf_cap_rule(m):
        return hours_manuf_A * m.xA + hours_manuf_B * m.xB + m.idle_manuf == cap_manuf

    model.manuf_cap = pyo.Constraint(rule=manuf_cap_rule)

    def asm_cap_rule(m):
        return hours_asm_A * m.xA + hours_asm_B * m.xB + m.idle_asm == cap_asm

    model.asm_cap = pyo.Constraint(rule=asm_cap_rule)

    def insp_cap_rule(m):
        return hours_insp_A * m.xA + hours_insp_B * m.xB + m.idle_insp == cap_insp

    model.insp_cap = pyo.Constraint(rule=insp_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"products":["A","B"],"processes":["manuf","asm","insp"]},"params":["price_A","price_B","hours_manuf_A","hours_asm_A","hours_insp_A","hours_manuf_B","hours_asm_B","hours_insp_B","cap_manuf","cap_asm","cap_insp","cost_manuf","cost_asm","cost_insp","profit_target","min_A_target"],"variables":{"production[products]":"nonnegative_integer","idle[processes]":"nonnegative_real","profit_shortfall":"nonnegative_real","A_shortfall":"nonnegative_real"},"expressions":{"usage[s]":"sum(hours[s,t]*production[t] for t in products)","profit":"sum(price[t]*production[t] for t in products)-sum(cost[s]*usage[s] for s in processes)"},"constraints":["usage[s]+idle[s]=capacity[s] for each process s; nonnegative idle prohibits overtime","profit+profit_shortfall>=profit_target","production[A]+A_shortfall>=min_A_target","after priority 1, fix profit_shortfall to its optimal value","after priority 2, fix A_shortfall to its optimal value"],"objective":{"sense":"lexicographic_minimize","priorities":["profit_shortfall","A_shortfall","sum(cost[s]*idle[s] for s in processes)"],"returned_objective":"priority 3 weighted idle cost at the lexicographic optimum"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the integer, preemptive goal-programming production model."""
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=("A", "B"), ordered=True)
    model.processes = pyo.Set(
        initialize=("manuf", "asm", "insp"), ordered=True
    )

    model.price = pyo.Param(
        model.products,
        initialize={
            "A": params["price_A"],
            "B": params["price_B"],
        },
    )
    model.hours = pyo.Param(
        model.processes,
        model.products,
        initialize={
            ("manuf", "A"): params["hours_manuf_A"],
            ("asm", "A"): params["hours_asm_A"],
            ("insp", "A"): params["hours_insp_A"],
            ("manuf", "B"): params["hours_manuf_B"],
            ("asm", "B"): params["hours_asm_B"],
            ("insp", "B"): params["hours_insp_B"],
        },
    )
    model.capacity = pyo.Param(
        model.processes,
        initialize={
            "manuf": params["cap_manuf"],
            "asm": params["cap_asm"],
            "insp": params["cap_insp"],
        },
    )
    model.hourly_cost = pyo.Param(
        model.processes,
        initialize={
            "manuf": params["cost_manuf"],
            "asm": params["cost_asm"],
            "insp": params["cost_insp"],
        },
    )
    model.profit_target = pyo.Param(initialize=params["profit_target"])
    model.min_A_target = pyo.Param(initialize=params["min_A_target"])

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.idle = pyo.Var(model.processes, domain=pyo.NonNegativeReals)
    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.A_shortfall = pyo.Var(domain=pyo.NonNegativeReals)

    def usage_rule(current_model, process):
        return sum(
            current_model.hours[process, product]
            * current_model.production[product]
            for product in current_model.products
        )

    model.usage = pyo.Expression(model.processes, rule=usage_rule)

    model.profit = pyo.Expression(
        expr=sum(
            model.price[product] * model.production[product]
            for product in model.products
        )
        - sum(
            model.hourly_cost[process] * model.usage[process]
            for process in model.processes
        )
    )
    model.weighted_idle = pyo.Expression(
        expr=sum(
            model.hourly_cost[process] * model.idle[process]
            for process in model.processes
        )
    )

    def capacity_balance_rule(current_model, process):
        return (
            current_model.usage[process] + current_model.idle[process]
            == current_model.capacity[process]
        )

    model.capacity_balance = pyo.Constraint(
        model.processes, rule=capacity_balance_rule
    )
    model.profit_goal = pyo.Constraint(
        expr=model.profit + model.profit_shortfall >= model.profit_target
    )
    model.production_goal = pyo.Constraint(
        expr=model.production["A"] + model.A_shortfall >= model.min_A_target
    )

    model.goal_objective = pyo.Objective(
        expr=model.profit_shortfall, sense=pyo.minimize
    )

    def solve_current_priority():
        try:
            Highs().solve(model)
        except RuntimeError as exc:
            # APPsi raises this when it cannot load a feasible solution.
            # Unexpected runtime errors are allowed to propagate.
            if "feasible solution was not found" in str(exc).lower():
                return {"objective": None, "status": "no_feasible_solution"}
            raise

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        return {"objective": obj_val, "status": "optimal"}

    # Priority 1: minimize the unmet profit target.
    result = solve_current_priority()
    if result["objective"] is None:
        return result

    model.preserve_profit_priority = pyo.Constraint(
        expr=model.profit_shortfall == result["objective"]
    )

    # Priority 2: minimize the unmet type A target without degrading priority 1.
    model.goal_objective.set_value(model.A_shortfall)
    result = solve_current_priority()
    if result["objective"] is None:
        return result

    model.preserve_A_priority = pyo.Constraint(
        expr=model.A_shortfall == result["objective"]
    )

    # Priority 3: minimize cost-weighted idle time, preserving both prior goals.
    model.goal_objective.set_value(model.weighted_idle)
    return solve_current_priority()
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_A = params["price_A"]
    price_B = params["price_B"]
    hours_manuf_A = params["hours_manuf_A"]
    hours_asm_A = params["hours_asm_A"]
    hours_insp_A = params["hours_insp_A"]
    hours_manuf_B = params["hours_manuf_B"]
    hours_asm_B = params["hours_asm_B"]
    hours_insp_B = params["hours_insp_B"]
    cap_manuf = params["cap_manuf"]
    cap_asm = params["cap_asm"]
    cap_insp = params["cap_insp"]
    cost_manuf = params["cost_manuf"]
    cost_asm = params["cost_asm"]
    cost_insp = params["cost_insp"]
    profit_target = params["profit_target"]
    min_A_target = params["min_A_target"]

    model = gp.Model("motorcycle_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: production quantities
    x_A = model.addVar(lb=0.0, name="x_A")
    x_B = model.addVar(lb=0.0, name="x_B")

    # Cost per unit
    unit_cost_A = (hours_manuf_A * cost_manuf
                   + hours_asm_A * cost_asm
                   + hours_insp_A * cost_insp)
    unit_cost_B = (hours_manuf_B * cost_manuf
                   + hours_asm_B * cost_asm
                   + hours_insp_B * cost_insp)

    unit_profit_A = price_A - unit_cost_A
    unit_profit_B = price_B - unit_cost_B

    # Goal deviation variables (non-negative)
    # p1: profit >= profit_target
    d1_neg = model.addVar(lb=0.0, name="d1_neg")  # under-achievement of profit
    d1_pos = model.addVar(lb=0.0, name="d1_pos")  # over-achievement of profit

    # p2: x_A >= min_A_target
    d2_neg = model.addVar(lb=0.0, name="d2_neg")  # under-achievement of min_A
    d2_pos = model.addVar(lb=0.0, name="d2_pos")  # over-achievement of min_A

    # p3: minimize idle time for each process (no overtime allowed)
    # idle_manuf = cap_manuf - hours_manuf_A*x_A - hours_manuf_B*x_B >= 0
    # idle_asm   = cap_asm   - hours_asm_A*x_A   - hours_asm_B*x_B   >= 0
    # idle_insp  = cap_insp  - hours_insp_A*x_A  - hours_insp_B*x_B  >= 0
    # Deviation variables for capacity constraints (only underutilization / idle)
    d3_manuf_neg = model.addVar(lb=0.0, name="d3_manuf_neg")  # idle time in manufacturing
    d3_manuf_pos = model.addVar(lb=0.0, name="d3_manuf_pos")  # overtime (must be 0)
    d3_asm_neg = model.addVar(lb=0.0, name="d3_asm_neg")      # idle time in assembly
    d3_asm_pos = model.addVar(lb=0.0, name="d3_asm_pos")      # overtime (must be 0)
    d3_insp_neg = model.addVar(lb=0.0, name="d3_insp_neg")    # idle time in inspection
    d3_insp_pos = model.addVar(lb=0.0, name="d3_insp_pos")    # overtime (must be 0)

    # Goal constraints
    # p1: profit deviation
    model.addConstr(
        unit_profit_A * x_A + unit_profit_B * x_B - d1_pos + d1_neg == profit_target,
        name="goal_profit"
    )

    # p2: min type A production
    model.addConstr(
        x_A - d2_pos + d2_neg == min_A_target,
        name="goal_min_A"
    )

    # p3: capacity usage (no overtime means d_pos must be 0, enforced via constraint)
    model.addConstr(
        hours_manuf_A * x_A + hours_manuf_B * x_B + d3_manuf_neg - d3_manuf_pos == cap_manuf,
        name="goal_manuf"
    )
    model.addConstr(
        hours_asm_A * x_A + hours_asm_B * x_B + d3_asm_neg - d3_asm_pos == cap_asm,
        name="goal_asm"
    )
    model.addConstr(
        hours_insp_A * x_A + hours_insp_B * x_B + d3_insp_neg - d3_insp_pos == cap_insp,
        name="goal_insp"
    )

    # No overtime allowed: force positive deviations (overtime) to zero
    model.addConstr(d3_manuf_pos == 0, name="no_overtime_manuf")
    model.addConstr(d3_asm_pos == 0, name="no_overtime_asm")
    model.addConstr(d3_insp_pos == 0, name="no_overtime_insp")

    # Preemptive goal programming via weighted objective over all goals.
    # Priority structure: p1 >> p2 >> p3
    # Use large penalty weights to encode priority: w_p1 >> w_p2 >> w_p3
    # w_p1 = M^2, w_p2 = M, w_p3 = cost weights (normalized small)
    # M chosen large enough to dominate lower-priority terms.
    big_M1 = 1e8  # priority 1 weight
    big_M2 = 1e4  # priority 2 weight

    # p3 weights are the hourly costs of each process
    obj = (big_M1 * d1_neg
           + big_M2 * d2_neg
           + cost_manuf * d3_manuf_neg
           + cost_asm * d3_asm_neg
           + cost_insp * d3_insp_neg)

    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 194.66666666666669 (optimal) | 272.0 (optimal) | 194.66666666666666 (optimal) |
| 1 | 64.66010321403353 (optimal) | 284.83907094673305 (optimal) | 64.66010321403348 (optimal) |
| 2 | 445895.6553238151 (optimal) | 1541.026809733452 (optimal) | 45701.93603041905 (optimal) |
| 3 | 78.25237442123105 (optimal) | 239.63948022841458 (optimal) | 78.25237442123105 (optimal) |
| 4 | 108069.96023937372 (optimal) | 739.1777912824887 (optimal) | 11299.00676425163 (optimal) |
| 5 | 213.94258829854857 (optimal) | 427.3754233180098 (optimal) | 213.94258829854857 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 194.66666666666669 (optimal) | 272.0 (optimal) | 194.66666666666666 (optimal) |
| 1 | 64.66010321403353 (optimal) | 284.83907094673305 (optimal) | 64.66010321403348 (optimal) |
| 2 | 445895.6553238151 (optimal) | 1541.026809733452 (optimal) | 45701.93603041905 (optimal) |
| 3 | 78.25237442123105 (optimal) | 239.63948022841458 (optimal) | 78.25237442123105 (optimal) |
| 4 | 108069.96023937372 (optimal) | 739.1777912824887 (optimal) | 11299.00676425163 (optimal) |
| 5 | 213.94258829854857 (optimal) | 427.3754233180098 (optimal) | 213.94258829854857 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 3. om_industryor_14 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_14` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 14) |
| Problem class (OptiMind) | ['Lot-Sizing Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 141.0 |
| Answer (OptiMind) | 134 |
| Rules that certify it | panel_base_2of3 141.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A certain factory needs to use a special tool over $n$ planning stages. At stage $j$, $r_j$ specialized tools are needed. At the end of this stage, all tools used within this stage must be sent for repair before they can be reused. There are two repair methods: one is slow repair, which is cheaper (costs $b$ per tool) but takes longer ($p$ stages to return, e.g. if a tool goes to repair after stage 1, it will return at stage 1+p); the other is fast repair, which costs $c$ per tool $(c > b)$ and is faster, requiring only $q$ stages to return $(q < p)$. If the repaired tools cannot meet the needs, new ones must be purchased, with a cost of $a$ per new tool $(a > c)$. This special tool will no longer be used after $n$ stages. Determine an optimal plan for purchasing and repairing the tools to minimize the cost spent on tools during the planning period.\n\nn = 10  # number of stages\nr = [3, 5, 2, 4, 6, 5, 4, 3, 2, 1]  # tool requirements per stage, indexing starts at 1\na = 10  # cost of buying a new tool\nb = 1   # cost of slow repair\nc = 3   # cost of fast repair\np = 3   # slow repair duration\nq = 1   # fast repair duration
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"a": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"b": {"base":1,"perturb":{"mode":"abs","lo":0.0,"hi":6.0,"integer":false}}
"c": {"base":3,"perturb":{"mode":"abs","lo":0.0,"hi":10.0,"integer":false}}
"p": {"base":3,"perturb":{"mode":"abs","lo":2.0,"hi":6.0,"integer":true}}
"q": {"base":1,"perturb":{"mode":"abs","lo":1.0,"hi":4.0,"integer":true}}
"r": {"base":[3,5,2,4,6,5,4,3,2,1],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 10
    stages = list(range(1, n + 1))

    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]

    req = {j: r[j - 1] for j in stages}
    horizon = range(1, n + 1)

    model = pyo.ConcreteModel()

    # x[j]: new tools purchased for use at stage j
    model.x = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)

    # s[i,j]: tools that finish slow repair (sent after stage i) and return usable at stage j = i + p
    # indices: i in 1..n-p, j = i + p
    slow_pairs = [(i, i + p) for i in horizon if i + p <= n]
    model.slow = pyo.Var(slow_pairs, domain=pyo.NonNegativeIntegers)

    # f[i,j]: tools that finish fast repair (sent after stage i) and return usable at stage j = i + q
    fast_pairs = [(i, i + q) for i in horizon if i + q <= n]
    model.fast = pyo.Var(fast_pairs, domain=pyo.NonNegativeIntegers)

    # Availability: at each stage j, supply >= requirement
    def avail_rule(m, j):
        supply = m.x[j]
        for (i, jj) in slow_pairs:
            if jj == j:
                supply += m.slow[i, jj]
        for (i, jj) in fast_pairs:
            if jj == j:
                supply += m.fast[i, jj]
        return supply >= req[j]

    model.avail = pyo.Constraint(horizon, rule=avail_rule)

    # Tools used at stage j must be sent for repair afterward (all get repaired; no discarding).
    # Tools used at stage j = req[j] exactly (they are consumed/repaired). We need to allocate
    # each stage's tool usage to slow or fast repair.
    # For each stage j, the number of tools sent to slow + fast repair must equal req[j].
    # Slow repair after stage j is possible only if j + p <= n (if returns after horizon, useless but
    # still must be repaired — but repairing only costs money, so for minimization we allow "sent to
    # fast/slow" but if it returns after n it's wasted). To be safe and optimal, allow allocation.
    # However diverting to slow/fast when it returns after horizon costs more with no benefit, so
    # optimal won't do it. But we must ensure balance: total tools used at stage j = req[j].
    # Tools available at stage j are used; each used tool must be repaired (slow or fast).
    # We model repair-allocation variables per stage j: slow_j + fast_j = req[j].
    # But slow capacity in model is represented by slow[i,j+p] variables: tools returned.
    # So define: for stage j, slow-sent count = slow[i, i+p] where i=j; fast-sent = fast[j, j+q].
    # Since each stage sends exactly req[j] tools, we require:
    #   (slow var for j if exists) + (fast var for j if exists) = req[j]
    # But some stage j might not have either (if j+p > n and j+q > n). For n=10, p=3, q=1:
    # stage 10: fast return at 11 > 10 -> no fast var; slow return 13 > 10 -> no slow var.
    # Then tools used at stage 10 have nowhere to go. But they still must be repaired! Repair cost
    # must be incurred even if they never return. So we need separate cost/allocation variables.
    # Simpler: allocate slow/fast per stage regardless of return usability, but return vars only
    # for those that actually return within horizon.
    # Redesign: slow_sent[j] = tools sent to slow repair after stage j (cost b each).
    #           fast_sent[j] = tools sent to fast repair after stage j (cost c each).
    #           slow_sent[j] + fast_sent[j] = req[j]  (all used tools repaired)
    #           Returns: tools sent slow after stage i return at stage i+p (if <= n), usable then.
    #           tools sent fast after stage i return at i+q (if <= n), usable then.
    # This decouples "sending" from "returning within horizon".

    model.slow_sent = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)
    model.fast_sent = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)

    def split_rule(m, j):
        return m.slow_sent[j] + m.fast_sent[j] == req[j]

    model.split = pyo.Constraint(horizon, rule=split_rule)

    # Availability now uses slow_sent[i] for returns at i+p, fast_sent[i] for i+q
    def avail_rule2(m, j):
        supply = m.x[j]
        for i in horizon:
            if i + p == j:
                supply += m.slow_sent[i]
            if i + q == j:
                supply += m.fast_sent[i]
        return supply >= req[j]

    model.del_component(model.avail)
    model.avail = pyo.Constraint(horizon, rule=avail_rule2)

    # Remove old return vars (unused)
    model.del_component(model.slow)
    model.del_component(model.fast)

    # Objective: purchase cost + slow repair cost + fast repair cost
    def obj_rule(m):
        return (
            a * sum(m.x[j] for j in horizon)
            + b * sum(m.slow_sent[j] for j in horizon)
            + c * sum(m.fast_sent[j] for j in horizon)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T":"1..n","n":"len(params['r'])"},"params":{"a":"params['a']","b":"params['b']","c":"params['c']","p":"params['p'], positive integer","q":"params['q'], positive integer","r[j]":"params['r'][j-1], nonnegative integer"},"variables":{"purchase[j]":"nonnegative integer","slow[j]":"nonnegative integer, sent after stage j","fast[j]":"nonnegative integer, sent after stage j","inventory[j]":"nonnegative integer, unused serviceable tools after stage j"},"constraints":["slow[j]+fast[j]=r[j] for every j","inventory[j]=inventory[j-1]+purchase[j]+slow[j-p]+fast[j-q]-r[j] for every j; inventory[0]=0 and nonpositive-index repair terms are zero"],"objective":"minimize sum(a*purchase[j]+b*slow[j]+c*fast[j] for j in T)","horizon":"All used tools are sent for repair as required, including at the final stage; repair costs are charged when dispatched, even if return occurs after n."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p_input = params["p"]
    q_input = params["q"]
    requirements = list(params["r"])

    p = int(p_input)
    q = int(q_input)

    if p != p_input or q != q_input or not (0 < q < p):
        return {"objective": None, "status": "invalid_lead_times"}

    if not (0 <= b < c < a):
        return {"objective": None, "status": "invalid_costs"}

    if any(value < 0 or int(value) != value for value in requirements):
        return {"objective": None, "status": "invalid_requirements"}

    n = len(requirements)

    model = pyo.ConcreteModel()
    model.stages = pyo.Set(initialize=range(1, n + 1), ordered=True)

    model.purchase_cost = pyo.Param(initialize=a, within=pyo.NonNegativeReals)
    model.slow_cost = pyo.Param(initialize=b, within=pyo.NonNegativeReals)
    model.fast_cost = pyo.Param(initialize=c, within=pyo.NonNegativeReals)
    model.slow_lead = pyo.Param(initialize=p, within=pyo.PositiveIntegers)
    model.fast_lead = pyo.Param(initialize=q, within=pyo.PositiveIntegers)
    model.requirement = pyo.Param(
        model.stages,
        initialize={
            stage: requirements[stage - 1]
            for stage in range(1, n + 1)
        },
        within=pyo.NonNegativeIntegers,
    )

    model.purchase = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.slow = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.fast = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)
    model.inventory = pyo.Var(model.stages, domain=pyo.NonNegativeIntegers)

    def repair_dispatch_rule(instance, stage):
        return (
            instance.slow[stage] + instance.fast[stage]
            == instance.requirement[stage]
        )

    model.repair_dispatch = pyo.Constraint(
        model.stages, rule=repair_dispatch_rule
    )

    def inventory_balance_rule(instance, stage):
        previous_inventory = (
            instance.inventory[stage - 1] if stage > 1 else 0
        )
        slow_returns = (
            instance.slow[stage - p] if stage > p else 0
        )
        fast_returns = (
            instance.fast[stage - q] if stage > q else 0
        )
        return instance.inventory[stage] == (
            previous_inventory
            + instance.purchase[stage]
            + slow_returns
            + fast_returns
            - instance.requirement[stage]
        )

    model.inventory_balance = pyo.Constraint(
        model.stages, rule=inventory_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            (
                model.purchase_cost * model.purchase[stage]
                + model.slow_cost * model.slow[stage]
                + model.fast_cost * model.fast[stage]
            )
            for stage in model.stages
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
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]

    n = len(r)
    # stages are 1-indexed internally; use 0-indexed lists
    # r[j] = requirement at stage j+1 (0-indexed: stage index i means stage i+1)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables (0-indexed: i = 0..n-1 corresponds to stage i+1)
    # x[i]: new tools purchased at stage i
    # s[i]: tools sent to slow repair after stage i
    # f[i]: tools sent to fast repair after stage i
    x = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="x")
    s = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="s")
    f = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="f")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(a * x[i] + b * s[i] + c * f[i] for i in range(n)),
        GRB.MINIMIZE
    )

    # At each stage i, the tools available are:
    # - new tools purchased this stage: x[i]
    # - tools returned from slow repair: sent to slow repair after stage i-p (0-indexed: i-p),
    #   i.e., s[i-p] if i-p >= 0
    # - tools returned from fast repair: sent to fast repair after stage i-q (0-indexed: i-q),
    #   i.e., f[i-q] if i-q >= 0
    # These must cover the requirement r[i] (0-indexed)

    for i in range(n):
        available = x[i]
        # slow repair: tool sent after stage j (0-indexed) returns at stage j+p (0-indexed)
        # so returns at stage i if j = i - p
        j_slow = i - p
        if j_slow >= 0:
            available = available + s[j_slow]
        # fast repair: tool sent after stage j returns at stage j+q
        j_fast = i - q
        if j_fast >= 0:
            available = available + f[j_fast]

        model.addConstr(available >= r[i], name=f"demand_{i}")

    # After each stage i, tools used must all be sent to either slow or fast repair
    # (or discarded, but since there's no salvage value and tools cost money, optimal
    # solution won't discard — but to be correct we allow that tools used = r[i],
    # and we must send AT MOST r[i] to repair; we cannot send more than used)
    # Actually: tools available at stage i = x[i] + returned repairs
    # All r[i] tools used at stage i must be repaired; additional purchased/available tools
    # beyond r[i] could also be repaired or held. But there's no holding variable —
    # let's think more carefully.
    #
    # The correct formulation: at stage i, let avail[i] = x[i] + s[i-p] + f[i-q]
    # avail[i] >= r[i] (demand constraint)
    # Tools actually used = r[i]; excess tools (avail[i] - r[i]) can also be sent to repair.
    # s[i] + f[i] <= avail[i]  (can't send more to repair than available)
    # But also we might want s[i] + f[i] <= r[i] since only used tools need repair
    # and excess could be held... but there's no "hold" variable and holding is free.
    #
    # To handle holding properly we'd need inventory variables, but the standard
    # formulation for this classic problem assumes all tools in circulation are repaired.
    # Let's add: s[i] + f[i] <= avail[i], and also enforce that tools sent to repair
    # don't exceed what's available.

    # We'll track availability explicitly
    avail = {}
    for i in range(n):
        expr = x[i]
        if i - p >= 0:
            expr = expr + s[i - p]
        if i - q >= 0:
            expr = expr + f[i - q]
        avail[i] = expr

    for i in range(n):
        # Cannot send more tools to repair than are available
        model.addConstr(s[i] + f[i] <= avail[i], name=f"repair_cap_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 141.0 (optimal) | 141.0 (optimal) | 134.0 (optimal) |
| 1 | 176.16627836544257 (optimal) | none (invalid_lead_times) | 173.91531039540254 (optimal) |
| 2 | 136.33154528835766 (optimal) | none (invalid_costs) | 99.29178401308202 (optimal) |
| 3 | 117.08328560989277 (optimal) | none (invalid_lead_times) | 113.10289015731321 (optimal) |
| 4 | 240.87755222616377 (optimal) | 236.9493864471567 (optimal) | 228.8677175220315 (optimal) |
| 5 | 323.6102118084622 (optimal) | none (invalid_lead_times) | 272.5726343307635 (optimal) |

#### independent

Decision: UNINFORMATIVE; clique none; informative instances [0]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 141.0 (optimal) | 141.0 (optimal) | 134.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | none (invalid_lead_times) | 197.00397542723223 (optimal) |
| 2 | none (infeasible_or_unbounded) | none (invalid_requirements) | 268.74065110413363 (optimal) |
| 3 | none (infeasible_or_unbounded) | none (invalid_requirements) | 325.4328220475325 (optimal) |
| 4 | none (infeasible_or_unbounded) | none (invalid_requirements) | 168.34267853524057 (optimal) |
| 5 | none (infeasible_or_unbounded) | none (invalid_requirements) | 401.3253661646487 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 4. om_industryor_23 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_23` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 23) |
| Problem class (OptiMind) | ['PortfolioOptimization'] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 140000.0 |
| Answer (OptiMind) | 510000 |
| Rules that certify it | gate 140000.0, panel_base_2of3 140000.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
An investor plans to invest 100,000 yuan, with two investment options to choose from. The first investment guarantees a return of 0.7 yuan for every 1 yuan invested after one year. The second investment guarantees a return of 2 yuan for every 1 yuan invested after two years, but the investment time must be in multiples of two years. In order to maximize the investor's earnings by the end of the third year, how should the investments be made? Formulate this as a linear programming problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"total_capital": {"base":100000,"perturb":{"mode":"rel","r":0.5}}
"return_rate_option1": {"base":0.7,"perturb":{"mode":"abs","lo":-0.2,"hi":1.5,"integer":false}}
"return_rate_option2": {"base":2.0,"perturb":{"mode":"abs","lo":0.5,"hi":3.5,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    C = params["total_capital"]
    r1 = params["return_rate_option1"]
    r2 = params["return_rate_option2"]

    model = pyo.ConcreteModel()

    # Periods (years) 0..3
    model.T = pyo.Set(initialize=[0, 1, 2, 3])

    # x[t]: amount invested at start of year t (t in 0,1,2) in 1-year option
    model.x = pyo.Var(range(3), domain=pyo.NonNegativeReals)
    # y[t]: amount invested at start of year t (t in 0,1) in 2-year option
    model.y = pyo.Var(range(2), domain=pyo.NonNegativeReals)

    # Returns from prior investments available at start of each year
    # At t=0: capital C available
    # At t=1: capital not invested at t0 + r1 * x0
    # At t=2: leftover + r1*x1 + r2*y0
    # At t=3: leftover + r1*x2 + r2*y1

    # Cash-balance constraints
    def cash_balance_rule(m, t):
        if t == 0:
            return m.x[0] + m.y[0] == C
        elif t == 1:
            return m.x[1] + m.y[1] == r1 * m.x[0]
        elif t == 2:
            return m.x[2] == r1 * m.x[1] + r2 * m.y[0]
        else:
            return pyo.Constraint.Skip

    model.cash_balance = pyo.Constraint([0, 1, 2], rule=cash_balance_rule)

    # Final wealth at end of year 3
    def objective_rule(m):
        return r1 * m.x[2] + r2 * m.y[1]

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"T1":[0,1,2],"T2":[0,1]},"params":{"total_capital":"initial capital","return_rate_option1":"total payout per yuan after one year","return_rate_option2":"total payout per yuan after two years"},"variables":{"x1[t in T1]":"NonNegativeReals; one-year investment starting at time t","x2[t in T2]":"NonNegativeReals; two-year investment starting at time t"},"constraints":["x1[0]+x2[0]=total_capital","x1[1]+x2[1]=return_rate_option1*x1[0]","x1[2]=return_rate_option1*x1[1]+return_rate_option2*x2[0]"],"objective":"maximize return_rate_option1*x1[2]+return_rate_option2*x2[1]"}
#
# Time 0 is the beginning of the first year; time 3 is the horizon.
# All initial capital and intermediate payouts are reinvested.
# Only investments maturing by time 3 are permitted.
# Return rates are total payout multipliers, including any returned principal.
# Maximizing terminal wealth also maximizes profit because initial capital is fixed.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.T1 = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.T2 = pyo.Set(initialize=[0, 1], ordered=True)

    model.total_capital = pyo.Param(
        initialize=params["total_capital"],
        within=pyo.NonNegativeReals,
    )
    model.return_rate_option1 = pyo.Param(
        initialize=params["return_rate_option1"],
        within=pyo.NonNegativeReals,
    )
    model.return_rate_option2 = pyo.Param(
        initialize=params["return_rate_option2"],
        within=pyo.NonNegativeReals,
    )

    model.x1 = pyo.Var(model.T1, domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(model.T2, domain=pyo.NonNegativeReals)

    model.initial_balance = pyo.Constraint(
        expr=model.x1[0] + model.x2[0] == model.total_capital
    )
    model.year_one_balance = pyo.Constraint(
        expr=model.x1[1] + model.x2[1]
        == model.return_rate_option1 * model.x1[0]
    )
    model.year_two_balance = pyo.Constraint(
        expr=model.x1[2]
        == model.return_rate_option1 * model.x1[1]
        + model.return_rate_option2 * model.x2[0]
    )

    model.terminal_wealth = pyo.Objective(
        expr=model.return_rate_option1 * model.x1[2]
        + model.return_rate_option2 * model.x2[1],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.terminal_wealth))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    C = params["total_capital"]
    r1 = params["return_rate_option1"]   # total return per yuan, 1-year option
    r2 = params["return_rate_option2"]   # total return per yuan, 2-year option

    # Time points: start of year 1 (t=0), start of year 2 (t=1), start of year 3 (t=2)
    # x1[t]: yuan in 1-year option at start of year t+1 (matures one year later)
    # x2[t]: yuan in 2-year option at start of year t+1 (matures two years later)
    model = gp.Model("investment")
    model.Params.OutputFlag = 0

    x1 = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"x1_{t}") for t in range(3)}
    x2 = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"x2_{t}") for t in range(2)}
    # idle cash carried from one year-start to the next
    s = {t: model.addVar(lb=0, ub=GRB.INFINITY, name=f"slack_{t}") for t in range(3)}

    # Cash-flow balance at each year-start
    # t=0: initial capital is split between both options and idle cash
    model.addConstr(x1[0] + x2[0] + s[0] == C, "cash_t0")

    # t=1: available = idle from t=0 (nothing has matured yet)
    model.addConstr(x1[1] + x2[1] + s[1] == s[0], "cash_t1")

    # t=2: available = idle from t=1 + maturity of x1[0]
    model.addConstr(x1[2] + s[2] == s[1] + r1 * x1[0], "cash_t2")

    # Final wealth at end of year 3:
    # idle cash + maturities: x1[1] (end yr 2), x2[0] (end yr 2, held as cash),
    # x1[2] and x2[1] mature exactly at end of year 3.
    final_wealth = (
        s[2]
        + r1 * x1[1]
        + r2 * x2[0]
        + r1 * x1[2]
        + r2 * x2[1]
    )
    model.setObjective(final_wealth, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed: status {model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 140000.0 (optimal) | 140000.0 (optimal) | 200000.0 (optimal) |
| 1 | 5664.338524842099 (optimal) | 5664.338524842099 (optimal) | 150984.07263630806 (optimal) |
| 2 | 202138.6329182322 (optimal) | 202138.6329182322 (optimal) | 182979.43764865724 (optimal) |
| 3 | 32057.772025749942 (optimal) | 32057.772025749942 (optimal) | 245826.25934564671 (optimal) |
| 4 | 35029.282829941316 (optimal) | 35029.282829941316 (optimal) | 106810.60891154943 (optimal) |
| 5 | 38470.03242801435 (optimal) | 38470.03242801435 (optimal) | 128983.05827280134 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 140000.0 (optimal) | 140000.0 (optimal) | 200000.0 (optimal) |
| 1 | -23777.2308657739 (optimal) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: return_rate_option1[None] = '-0.15748171612146622', value type=<class 'float'>. \| Value not in parameter domain NonNegativeReals) | 150984.07263630806 (optimal) |
| 2 | 192494.56311093172 (optimal) | 192494.56311093172 (optimal) | 182979.43764865724 (optimal) |
| 3 | -12833.11023994608 (optimal) | none (crash:raise ValueError( \| ValueError: Invalid parameter value: return_rate_option1[None] = '-0.05220398452999256', value type=<class 'float'>. \| Value not in parameter domain NonNegativeReals) | 245826.25934564671 (optimal) |
| 4 | 18337.7320916236 (optimal) | 18337.7320916236 (optimal) | 106810.60891154943 (optimal) |
| 5 | 17802.75843052266 (optimal) | 17802.75843052266 (optimal) | 128983.05827280134 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
Looking at the statement and parameters:

- **total_capital = 100000**: The statement says "invest 100,000 yuan" — matches.
- **return_rate_option1 = 0.7**: The statement says "a return of 0.7 yuan for every 1 yuan invested after one year" — matches.
- **return_rate_option2 = 2.0**: The statement says "a return of 2 yuan for every 1 yuan invested after two years" — matches.

No mismatches or not-stated parameters.

{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "return_rate_option1",
      "extracted": 0.7,
      "stated": 1.7,
      "evidence": "The first investment guarantees a return of 0.7 yuan for every 1 yuan invested after one year"
    },
    {
      "parameter": "return_rate_option2",
      "extracted": 2.0,
      "stated": 3.0,
      "evidence": "The second investment guarantees a return of 2 yuan for every 1 yuan invested after two years"
    }
  ],
  "not_stated": []
}
```
````


## 5. om_industryor_25 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_25` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 25) |
| Problem class (OptiMind) | ['Factory Planning Problem', 'Production Planning Problem'] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 1146.5665024630541 |
| Answer (OptiMind) | 1146.4142 |
| Rules that certify it | gate 1146.5665024630541, panel_base_2of3 1146.5665024630541, ind_gate 1146.5665024630541 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A factory produces three types of products: I, II, and III. Each product needs to go through two processing procedures, A and B. The factory has two pieces of equipment that can complete process A, denoted as A1 and A2; it has three pieces of equipment that complete process B, denoted as B1, B2, and B3. Product I can be processed on any equipment for A and B; Product II can be processed on any A equipment but only on B1 for process B; Product III can only be processed on A2 and B2. Given the unit processing time on various machines, raw material costs, product sale prices, effective machine hours, and the costs of operating the machines at full capacity as shown in Table 1-4, the task is to arrange the optimal production plan to maximize the factory's profit.

Table 1-4
| Equipment  | Product I | Product II | Product III | Effective Machine Hours | Operating Costs at Full Capacity (Yuan) |
|------------|-----------|------------|-------------|--------------------------|------------------------------------------|
| A1         | 5         | 10         |             | 6000                     | 300                                      |
| A2         | 7         | 9          | 12          | 10000                    | 321                                      |
| B1         | 6         | 8          |             | 4000                     | 250                                      |
| B2         | 4         |            | 11          | 7000                     | 783                                      |
| B3         | 7         |            |             | 4000                     | 200                                      |
| Raw Material Cost (Yuan/Unit) | 0.25 | 0.35       | 0.50       |                          |                                          |
| Unit Price (Yuan/Unit)        | 1.25 | 2.00       | 2.80       |                          |                                          |
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"processing_time_I": {"base":[5,7,6,4,7],"perturb":{"mode":"rel","r":0.35}}
"processing_time_II": {"base":[10,9,8],"perturb":{"mode":"rel","r":0.35}}
"processing_time_III": {"base":[12,11],"perturb":{"mode":"rel","r":0.35}}
"effective_hours": {"base":[6000,10000,4000,7000,4000],"perturb":{"mode":"rel","r":0.5}}
"operating_cost_full": {"base":[300,321,250,783,200],"perturb":{"mode":"rel","r":0.5}}
"raw_material_cost": {"base":[0.25,0.35,0.5],"perturb":{"mode":"rel","r":0.6}}
"unit_price": {"base":[1.25,2.0,2.8],"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    products = ['I', 'II', 'III']
    machines_A = ['A1', 'A2']
    machines_B = ['B1', 'B2', 'B3']
    all_machines = machines_A + machines_B

    # Feasible machine-product assignments (process A)
    assign_A = {
        'I': ['A1', 'A2'],
        'II': ['A1', 'A2'],
        'III': ['A2'],
    }
    # Feasible machine-product assignments (process B)
    assign_B = {
        'I': ['B1', 'B2', 'B3'],
        'II': ['B1'],
        'III': ['B2'],
    }

    # Processing times read from params, stored as dicts keyed by machine
    pt_I = params["processing_time_I"]
    pt_II = params["processing_time_II"]
    pt_III = params["processing_time_III"]
    proc = {
        'I': pt_I,
        'II': pt_II,
        'III': pt_III,
    }

    eff_hours = params["effective_hours"]
    op_cost = params["operating_cost_full"]
    raw_cost = params["raw_material_cost"]
    price = params["unit_price"]

    model = pyo.ConcreteModel()

    # Total production quantity per product
    model.qty = pyo.Var(products, domain=pyo.NonNegativeReals)

    # Process-A allocation variable: xA[product, machine]
    xA_index = [(p, mk) for p in products for mk in assign_A[p]]
    model.xA = pyo.Var(xA_index, domain=pyo.NonNegativeReals)

    # Process-B allocation variable: xB[product, machine]
    xB_index = [(p, mk) for p in products for mk in assign_B[p]]
    model.xB = pyo.Var(xB_index, domain=pyo.NonNegativeReals)

    # Flow balance for process A: sum over A machines = qty
    def flow_A_rule(model, p):
        return sum(model.xA[p, mk] for mk in assign_A[p]) == model.qty[p]
    model.flow_A = pyo.Constraint(products, rule=flow_A_rule)

    # Flow balance for process B: sum over B machines = qty
    def flow_B_rule(model, p):
        return sum(model.xB[p, mk] for mk in assign_B[p]) == model.qty[p]
    model.flow_B = pyo.Constraint(products, rule=flow_B_rule)

    # Machine capacity (effective hours) constraints
    def cap_A_rule(model, mk):
        return sum(model.xA[p, mk] * proc[p][mk] for p in products
                   if mk in assign_A[p]) <= eff_hours[mk]
    model.cap_A = pyo.Constraint(machines_A, rule=cap_A_rule)

    def cap_B_rule(model, mk):
        return sum(model.xB[p, mk] * proc[p][mk] for p in products
                   if mk in assign_B[p]) <= eff_hours[mk]
    model.cap_B = pyo.Constraint(machines_B, rule=cap_B_rule)

    # Objective: maximize total profit
    # Revenue minus raw material cost minus operating costs
    revenue = sum(price[p] * model.qty[p] for p in products)
    material = sum(raw_cost[p] * model.qty[p] for p in products)
    operating = sum(op_cost[mk] for mk in all_machines)

    model.obj = pyo.Objective(
        expr=revenue - material - operating,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"products":["I","II","III"],"machines":["A1","A2","B1","B2","B3"],"stages":{"A":["A1","A2"],"B":["B1","B2","B3"]},"eligible_machines":{"I":["A1","A2","B1","B2","B3"],"II":["A1","A2","B1"],"III":["A2","B2"]},"arcs":"Eligible product-machine pairs with present, nonblank processing times."},"params":{"processing_time_I":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","processing_time_II":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","processing_time_III":"Machine-keyed mapping, five-machine sequence, or eligible-machine sequence.","effective_hours":"Machine-keyed mapping or sequence in machines order; positive.","operating_cost_full":"Machine-keyed mapping or sequence in machines order; nonnegative.","raw_material_cost":"Product-keyed mapping or sequence in products order; nonnegative.","unit_price":"Product-keyed mapping or sequence in products order; nonnegative."},"variables":{"production[p]":"NonNegativeReals","processed[p,e]":"NonNegativeReals on arcs"},"constraints":["For each product p and stage s: sum(processed[p,e] over applicable machines e in s) = production[p].","For each machine e: sum(processing_time[p,e]*processed[p,e] over applicable products p) <= effective_hours[e]."],"objective":"Maximize sum((unit_price[p]-raw_material_cost[p])*production[p]) - sum(operating_cost_full[e]*machine_load[e]/effective_hours[e]); operating costs are proportional to utilized capacity."}

from collections.abc import Mapping, Sequence

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _as_mapping(values, ordered_keys, label, eligible_keys=None):
    """Accept keyed inputs or positional inputs with documented ordering."""
    if isinstance(values, Mapping):
        return dict(values)

    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise TypeError(f"{label} must be a mapping or a sequence.")

    if len(values) == len(ordered_keys):
        return dict(zip(ordered_keys, values))

    if eligible_keys is not None and len(values) == len(eligible_keys):
        return dict(zip(eligible_keys, values))

    expected_lengths = {len(ordered_keys)}
    if eligible_keys is not None:
        expected_lengths.add(len(eligible_keys))

    expected = " or ".join(str(length) for length in sorted(expected_lengths))
    raise ValueError(f"{label} must contain {expected} entries.")


def solve(params):
    products = ("I", "II", "III")
    machines = ("A1", "A2", "B1", "B2", "B3")
    stages = {
        "A": ("A1", "A2"),
        "B": ("B1", "B2", "B3"),
    }
    eligible_machines = {
        "I": ("A1", "A2", "B1", "B2", "B3"),
        "II": ("A1", "A2", "B1"),
        "III": ("A2", "B2"),
    }

    processing_inputs = {
        "I": params["processing_time_I"],
        "II": params["processing_time_II"],
        "III": params["processing_time_III"],
    }
    hours_input = _as_mapping(
        params["effective_hours"], machines, "effective_hours"
    )
    operating_cost_input = _as_mapping(
        params["operating_cost_full"], machines, "operating_cost_full"
    )
    material_cost_input = _as_mapping(
        params["raw_material_cost"], products, "raw_material_cost"
    )
    price_input = _as_mapping(
        params["unit_price"], products, "unit_price"
    )

    processing_times = {}
    for product in products:
        entries = _as_mapping(
            processing_inputs[product],
            machines,
            f"processing_time_{product}",
            eligible_keys=eligible_machines[product],
        )
        for machine in eligible_machines[product]:
            value = entries.get(machine)
            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                continue
            processing_times[product, machine] = float(value)

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.machines = pyo.Set(initialize=machines, ordered=True)
    model.stages = pyo.Set(initialize=tuple(stages), ordered=True)
    model.processing_arcs = pyo.Set(
        dimen=2,
        initialize=tuple(processing_times),
        ordered=True,
    )

    model.processing_time = pyo.Param(
        model.processing_arcs,
        initialize=processing_times,
        within=pyo.PositiveReals,
    )
    model.effective_hours = pyo.Param(
        model.machines,
        initialize={
            machine: float(hours_input[machine])
            for machine in machines
        },
        within=pyo.PositiveReals,
    )
    model.operating_cost_full = pyo.Param(
        model.machines,
        initialize={
            machine: float(operating_cost_input[machine])
            for machine in machines
        },
        within=pyo.NonNegativeReals,
    )
    model.raw_material_cost = pyo.Param(
        model.products,
        initialize={
            product: float(material_cost_input[product])
            for product in products
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_price = pyo.Param(
        model.products,
        initialize={
            product: float(price_input[product])
            for product in products
        },
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )
    model.processed = pyo.Var(
        model.processing_arcs,
        domain=pyo.NonNegativeReals,
    )

    def stage_balance_rule(factory, product, stage):
        return sum(
            factory.processed[product, machine]
            for machine in stages[stage]
            if (product, machine) in factory.processing_arcs
        ) == factory.production[product]

    model.stage_balance = pyo.Constraint(
        model.products,
        model.stages,
        rule=stage_balance_rule,
    )

    def machine_load_rule(factory, machine):
        return sum(
            factory.processing_time[product, machine]
            * factory.processed[product, machine]
            for product in factory.products
            if (product, machine) in factory.processing_arcs
        )

    model.machine_load = pyo.Expression(
        model.machines,
        rule=machine_load_rule,
    )

    def capacity_rule(factory, machine):
        return (
            factory.machine_load[machine]
            <= factory.effective_hours[machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.machines,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (
                model.unit_price[product]
                - model.raw_material_cost[product]
            )
            * model.production[product]
            for product in model.products
        )
        - sum(
            model.operating_cost_full[machine]
            * model.machine_load[machine]
            / model.effective_hours[machine]
            for machine in model.machines
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Preserve unexpected solver exceptions.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # params values may be lists (positional) or dicts; normalize to dicts
    machines = ["A1", "A2", "B1", "B2", "B3"]
    products = ["I", "II", "III"]

    def to_dict(val, keys):
        if isinstance(val, dict):
            return val
        # assume list/tuple in same order as keys, skip None/missing entries
        return {k: v for k, v in zip(keys, val) if v is not None}

    pt_I_raw   = params["processing_time_I"]
    pt_II_raw  = params["processing_time_II"]
    pt_III_raw = params["processing_time_III"]
    eff_raw    = params["effective_hours"]
    op_raw     = params["operating_cost_full"]
    rm_raw     = params["raw_material_cost"]
    up_raw     = params["unit_price"]

    processing_time_I   = to_dict(pt_I_raw,   machines)   # A1,A2,B1,B2,B3
    processing_time_II  = to_dict(pt_II_raw,  ["A1","A2","B1"])
    processing_time_III = to_dict(pt_III_raw, ["A2","B2"])
    effective_hours     = to_dict(eff_raw,    machines)
    operating_cost_full = to_dict(op_raw,     machines)
    raw_material_cost   = to_dict(rm_raw,     products)
    unit_price          = to_dict(up_raw,     products)

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each product routed through each eligible machine
    # Product I on A process
    xI_A1 = model.addVar(lb=0, name="xI_A1")
    xI_A2 = model.addVar(lb=0, name="xI_A2")
    # Product I on B process
    xI_B1 = model.addVar(lb=0, name="xI_B1")
    xI_B2 = model.addVar(lb=0, name="xI_B2")
    xI_B3 = model.addVar(lb=0, name="xI_B3")

    # Product II on A process
    xII_A1 = model.addVar(lb=0, name="xII_A1")
    xII_A2 = model.addVar(lb=0, name="xII_A2")
    # Product II on B process (B1 only)
    xII_B1 = model.addVar(lb=0, name="xII_B1")

    # Product III on A process (A2 only)
    xIII_A2 = model.addVar(lb=0, name="xIII_A2")
    # Product III on B process (B2 only)
    xIII_B2 = model.addVar(lb=0, name="xIII_B2")

    model.update()

    # Flow balance: units entering process A must equal units entering process B for each product
    model.addConstr(xI_A1 + xI_A2 == xI_B1 + xI_B2 + xI_B3, name="balance_I")
    model.addConstr(xII_A1 + xII_A2 == xII_B1,               name="balance_II")
    model.addConstr(xIII_A2 == xIII_B2,                       name="balance_III")

    # Machine capacity constraints
    model.addConstr(
        processing_time_I["A1"] * xI_A1 + processing_time_II["A1"] * xII_A1
        <= effective_hours["A1"],
        name="cap_A1"
    )
    model.addConstr(
        processing_time_I["A2"] * xI_A2 + processing_time_II["A2"] * xII_A2
        + processing_time_III["A2"] * xIII_A2
        <= effective_hours["A2"],
        name="cap_A2"
    )
    model.addConstr(
        processing_time_I["B1"] * xI_B1 + processing_time_II["B1"] * xII_B1
        <= effective_hours["B1"],
        name="cap_B1"
    )
    model.addConstr(
        processing_time_I["B2"] * xI_B2 + processing_time_III["B2"] * xIII_B2
        <= effective_hours["B2"],
        name="cap_B2"
    )
    model.addConstr(
        processing_time_I["B3"] * xI_B3
        <= effective_hours["B3"],
        name="cap_B3"
    )

    # Operating cost rate per machine-hour used = full_capacity_cost / effective_hours
    op_cost_rate = {m: operating_cost_full[m] / effective_hours[m] for m in machines}

    hours_A1 = processing_time_I["A1"] * xI_A1 + processing_time_II["A1"] * xII_A1
    hours_A2 = (processing_time_I["A2"] * xI_A2 + processing_time_II["A2"] * xII_A2
                + processing_time_III["A2"] * xIII_A2)
    hours_B1 = processing_time_I["B1"] * xI_B1 + processing_time_II["B1"] * xII_B1
    hours_B2 = processing_time_I["B2"] * xI_B2 + processing_time_III["B2"] * xIII_B2
    hours_B3 = processing_time_I["B3"] * xI_B3

    total_operating_cost = (
        op_cost_rate["A1"] * hours_A1 +
        op_cost_rate["A2"] * hours_A2 +
        op_cost_rate["B1"] * hours_B1 +
        op_cost_rate["B2"] * hours_B2 +
        op_cost_rate["B3"] * hours_B3
    )

    # Total units of each product produced
    total_I   = xI_A1 + xI_A2
    total_II  = xII_A1 + xII_A2
    total_III = xIII_A2

    revenue  = (unit_price["I"] * total_I
                + unit_price["II"] * total_II
                + unit_price["III"] * total_III)

    raw_cost = (raw_material_cost["I"] * total_I
                + raw_material_cost["II"] * total_II
                + raw_material_cost["III"] * total_III)

    profit = revenue - raw_cost - total_operating_cost

    model.setObjective(profit, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 1146.5665024630541 (optimal) | 1146.566502463054 (optimal) |
| 1 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 699.1868309969939 (optimal) | 699.1868309969938 (optimal) |
| 2 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 2003.7201727958031 (optimal) | 2003.7201727958038 (optimal) |
| 3 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 2321.0152176614524 (optimal) | 2321.0152176614524 (optimal) |
| 4 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 869.135275847118 (optimal) | 869.135275847118 (optimal) |
| 5 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 3493.641652085123 (optimal) | 3493.6416520851244 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 1146.5665024630541 (optimal) | 1146.566502463054 (optimal) |
| 1 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 699.1868309969939 (optimal) | 699.1868309969938 (optimal) |
| 2 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 2003.7201727958031 (optimal) | 2003.7201727958038 (optimal) |
| 3 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 2321.0152176614524 (optimal) | 2321.0152176614524 (optimal) |
| 4 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 869.135275847118 (optimal) | 869.135275847118 (optimal) |
| 5 | none (crash:return sum(model.xA[p, mk] * proc[p][mk] for p in products \| ~~~~~~~^^^^ \| TypeError: list indices must be integers or slices, not str) | 3493.641652085123 (optimal) | 3493.6416520851244 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 6. om_industryor_43 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_43` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 43) |
| Problem class (OptiMind) | ['Production Planning Problem', 'Profit Maximization Problem'] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 715.0 |
| Answer (OptiMind) | 712 |
| Rules that certify it | panel_base_2of3 715.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A factory produces three types of products, A, B, and C. Each unit of product A requires 1 hour for technical preparation, 10 hours of direct labor, and 3 kg of materials. Each unit of product B requires 2 hours for technical preparation, 4 hours of labor, and 2 kg of materials. Each unit of product C requires 1 hour for technical preparation, 5 hours of labor, and 1 kg of materials. The available technical preparation time is 100 hours, labor time is 700 hours, and materials are 400 kg. The company offers larger discounts for bulk purchases, as detailed in Table 1-22. Determine the company's production plan to maximize profit.
Table 1-22
| Product A       |           | Product B       |           | Product C       |           |
|:---------------|:---------:|:---------------|:---------:|:---------------|:---------:|
| Sales Volume (pieces) | Profit (yuan) | Sales Volume (pieces) | Profit (yuan) | Sales Volume (pieces) | Profit (yuan) |
| 0 ~ 40         | 10        | 0 ~ 50         | 6         | 0 ~ 100        | 5         |
| 40 ~ 100       | 9         | 50 ~ 100       | 4         | Above 100      | 4         |
| 100 ~ 150      | 8         | Above 100      | 3         |                |           |
| Above 150      | 7         |                |           |                |           |
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"prep_A": {"base":1,"perturb":{"mode":"rel","r":0.3}}
"prep_B": {"base":2,"perturb":{"mode":"rel","r":0.3}}
"prep_C": {"base":1,"perturb":{"mode":"rel","r":0.3}}
"labor_A": {"base":10,"perturb":{"mode":"rel","r":0.3}}
"labor_B": {"base":4,"perturb":{"mode":"rel","r":0.3}}
"labor_C": {"base":5,"perturb":{"mode":"rel","r":0.3}}
"material_A": {"base":3,"perturb":{"mode":"rel","r":0.3}}
"material_B": {"base":2,"perturb":{"mode":"rel","r":0.3}}
"material_C": {"base":1,"perturb":{"mode":"rel","r":0.3}}
"tech_capacity": {"base":100,"perturb":{"mode":"rel","r":0.25}}
"labor_capacity": {"base":700,"perturb":{"mode":"rel","r":0.25}}
"material_capacity": {"base":400,"perturb":{"mode":"rel","r":0.25}}
"profit_A_tiers": {"base":[10,9,8,7],"perturb":{"mode":"rel","r":0.2}}
"profit_B_tiers": {"base":[6,4,3],"perturb":{"mode":"rel","r":0.2}}
"profit_C_tiers": {"base":[5,4],"perturb":{"mode":"rel","r":0.2}}
"tier_breakpoints_A": {"base":[40,100,150],"perturb":{"mode":"abs","lo":0.0,"hi":200.0,"integer":true}}
"tier_breakpoints_B": {"base":[50,100],"perturb":{"mode":"abs","lo":0.0,"hi":150.0,"integer":true}}
"tier_breakpoints_C": {"base":[100],"perturb":{"mode":"abs","lo":0.0,"hi":200.0,"integer":true}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Products
    products = ['A', 'B', 'C']

    # Tier data per product
    tier_data = {
        'A': (list(params["tier_breakpoints_A"]), list(params["profit_A_tiers"])),
        'B': (list(params["tier_breakpoints_B"]), list(params["profit_B_tiers"])),
        'C': (list(params["tier_breakpoints_C"]), list(params["profit_C_tiers"])),
    }

    # Production quantities
    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    # Piecewise segment variables
    # For each product, segments: [0, bp0], [bp0, bp1], ..., [bp_last, +inf]
    # Number of segments = len(breakpoints) + 1
    seg_vars = {}
    model.segments = pyo.Set(initialize=[
        (p, k) for p in products for k in range(len(tier_data[p][0]) + 1)
    ])
    model.y = pyo.Var(model.segments, domain=pyo.NonNegativeReals)

    # Link x = sum of segments
    def link_rule(m, p):
        return m.x[p] == sum(m.y[(p, k)] for k in range(len(tier_data[p][0]) + 1))
    model.link = pyo.Constraint(products, rule=link_rule)

    # Upper bounds on segment sizes (binary-free LP formulation via big-M style):
    # To model concave piecewise profit correctly we need proper upper bounds.
    # Since per-unit profit decreases with volume tier, the profit function is concave,
    # so the natural LP relaxation (allowing segment fill out of order) is exact:
    # the solver will fill cheaper (higher profit) segments first automatically.
    # Still we impose segment upper bounds for finite segments.
    finite_seg_bound = {}
    for p in products:
        bps = tier_data[p][0]
        for k in range(len(bps)):
            if k == 0:
                upper = bps[0]
            else:
                upper = bps[k] - bps[k-1]
            finite_seg_bound[(p, k)] = upper

    # Bounds: finite segments bounded, last segment unbounded (NonNegativeReals)
    for (p, k), ub in finite_seg_bound.items():
        model.y[(p, k)].setub(ub)

    # Resource constraints
    model.tech = pyo.Constraint(
        expr=params["prep_A"] * model.x['A']
        + params["prep_B"] * model.x['B']
        + params["prep_C"] * model.x['C']
        <= params["tech_capacity"]
    )
    model.labor = pyo.Constraint(
        expr=params["labor_A"] * model.x['A']
        + params["labor_B"] * model.x['B']
        + params["labor_C"] * model.x['C']
        <= params["labor_capacity"]
    )
    model.material = pyo.Constraint(
        expr=params["material_A"] * model.x['A']
        + params["material_B"] * model.x['B']
        + params["material_C"] * model.x['C']
        <= params["material_capacity"]
    )

    # Objective: maximize total profit from segments
    def obj_rule(m):
        total = 0
        for p in products:
            profits = tier_data[p][1]
            for k in range(len(profits)):
                total += profits[k] * m.y[(p, k)]
        return total
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))

    return {'objective': obj_val, 'status': 'optimal'}
```

#### B-structured.py

```python
# IR: {"sets":{"products":["A","B","C"],"resources":["prep","labor","material"],"tiers":{"A":[0,1,2,3],"B":[0,1,2],"C":[0,1]}},"params":["prep_A","prep_B","prep_C","labor_A","labor_B","labor_C","material_A","material_B","material_C","tech_capacity","labor_capacity","material_capacity","profit_A_tiers","profit_B_tiers","profit_C_tiers","tier_breakpoints_A","tier_breakpoints_B","tier_breakpoints_C"],"interpretation":"Integer production quantities; the selected sales-volume tier determines per-unit profit on all units. Breakpoints belong to the lower-volume tier.","derived":{"L[p,0]":"0","L[p,t>0]":"floor(breakpoint[p,t-1])+1","U[p,t<last]":"min(floor(breakpoint[p,t]),production_bound[p])","production_bound[p]":"minimum floor(capacity[r]/usage[r,p]) over positive resource usages; if none, unbounded when final-tier profit is positive, otherwise floor(last_breakpoint[p])+1"},"variables":{"selected[p,t]":"Binary","quantity[p,t]":"NonNegativeIntegers"},"constraints":["sum_t selected[p,t] = 1 for each product p","quantity[p,t] >= L[p,t]*selected[p,t]","quantity[p,t] <= U[p,t]*selected[p,t], with U[p,last]=production_bound[p]","sum_(p,t) usage[r,p]*quantity[p,t] <= capacity[r] for each resource r"],"objective":"maximize sum_(p,t) profit[p,t]*quantity[p,t]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B", "C")
    resources = ("prep", "labor", "material")

    usage = {
        ("prep", "A"): float(params["prep_A"]),
        ("prep", "B"): float(params["prep_B"]),
        ("prep", "C"): float(params["prep_C"]),
        ("labor", "A"): float(params["labor_A"]),
        ("labor", "B"): float(params["labor_B"]),
        ("labor", "C"): float(params["labor_C"]),
        ("material", "A"): float(params["material_A"]),
        ("material", "B"): float(params["material_B"]),
        ("material", "C"): float(params["material_C"]),
    }
    capacity = {
        "prep": float(params["tech_capacity"]),
        "labor": float(params["labor_capacity"]),
        "material": float(params["material_capacity"]),
    }
    profits = {
        "A": tuple(float(value) for value in params["profit_A_tiers"]),
        "B": tuple(float(value) for value in params["profit_B_tiers"]),
        "C": tuple(float(value) for value in params["profit_C_tiers"]),
    }
    breakpoints = {
        "A": tuple(float(value) for value in params["tier_breakpoints_A"]),
        "B": tuple(float(value) for value in params["tier_breakpoints_B"]),
        "C": tuple(float(value) for value in params["tier_breakpoints_C"]),
    }
    tier_counts = {"A": 4, "B": 3, "C": 2}

    numeric_values = (
        list(usage.values())
        + list(capacity.values())
        + [value for values in profits.values() for value in values]
        + [value for values in breakpoints.values() for value in values]
    )
    if not all(math.isfinite(value) for value in numeric_values):
        return {"objective": None, "status": "invalid_parameters"}

    if any(value < 0 for value in usage.values()):
        return {"objective": None, "status": "invalid_parameters"}

    for product in products:
        thresholds = breakpoints[product]
        if (
            len(profits[product]) != tier_counts[product]
            or len(thresholds) != tier_counts[product] - 1
            or any(value < 0 for value in thresholds)
            or any(
                thresholds[position] >= thresholds[position + 1]
                for position in range(len(thresholds) - 1)
            )
        ):
            return {"objective": None, "status": "invalid_parameters"}

    if any(value < 0 for value in capacity.values()):
        return {"objective": None, "status": "infeasible"}

    production_bounds = {}
    for product in products:
        resource_bounds = [
            math.floor(capacity[resource] / usage[resource, product])
            for resource in resources
            if usage[resource, product] > 0
        ]
        if resource_bounds:
            production_bounds[product] = min(resource_bounds)
        elif profits[product][-1] > 0:
            return {"objective": None, "status": "unbounded"}
        else:
            # With no resource consumption and nonpositive final-tier
            # profit, increasing quantity beyond this point cannot help.
            production_bounds[product] = (
                math.floor(breakpoints[product][-1]) + 1
            )

    tier_pairs = [
        (product, tier)
        for product in products
        for tier in range(tier_counts[product])
    ]

    lower_bounds = {}
    upper_bounds = {}
    for product, tier in tier_pairs:
        lower_bounds[product, tier] = (
            0
            if tier == 0
            else math.floor(breakpoints[product][tier - 1]) + 1
        )
        upper_bounds[product, tier] = (
            min(
                math.floor(breakpoints[product][tier]),
                production_bounds[product],
            )
            if tier < tier_counts[product] - 1
            else production_bounds[product]
        )

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.resources = pyo.Set(initialize=resources, ordered=True)
    model.tier_pairs = pyo.Set(
        dimen=2, initialize=tier_pairs, ordered=True
    )

    model.selected = pyo.Var(model.tier_pairs, domain=pyo.Binary)
    model.quantity = pyo.Var(
        model.tier_pairs, domain=pyo.NonNegativeIntegers
    )

    def tier_choice_rule(instance, product):
        return sum(
            instance.selected[product, tier]
            for tier in range(tier_counts[product])
        ) == 1

    model.tier_choice = pyo.Constraint(
        model.products, rule=tier_choice_rule
    )

    def tier_lower_rule(instance, product, tier):
        return instance.quantity[product, tier] >= (
            lower_bounds[product, tier]
            * instance.selected[product, tier]
        )

    model.tier_lower = pyo.Constraint(
        model.tier_pairs, rule=tier_lower_rule
    )

    def tier_upper_rule(instance, product, tier):
        return instance.quantity[product, tier] <= (
            upper_bounds[product, tier]
            * instance.selected[product, tier]
        )

    model.tier_upper = pyo.Constraint(
        model.tier_pairs, rule=tier_upper_rule
    )

    def resource_limit_rule(instance, resource):
        return sum(
            usage[resource, product] * instance.quantity[product, tier]
            for product, tier in instance.tier_pairs
        ) <= capacity[resource]

    model.resource_limit = pyo.Constraint(
        model.resources, rule=resource_limit_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profits[product][tier] * model.quantity[product, tier]
            for product, tier in model.tier_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prep_A = params["prep_A"]
    prep_B = params["prep_B"]
    prep_C = params["prep_C"]
    labor_A = params["labor_A"]
    labor_B = params["labor_B"]
    labor_C = params["labor_C"]
    material_A = params["material_A"]
    material_B = params["material_B"]
    material_C = params["material_C"]
    tech_capacity = params["tech_capacity"]
    labor_capacity = params["labor_capacity"]
    material_capacity = params["material_capacity"]
    profit_A_tiers = params["profit_A_tiers"]
    profit_B_tiers = params["profit_B_tiers"]
    profit_C_tiers = params["profit_C_tiers"]
    tier_breakpoints_A = params["tier_breakpoints_A"]
    tier_breakpoints_B = params["tier_breakpoints_B"]
    tier_breakpoints_C = params["tier_breakpoints_C"]

    # tier_breakpoints_A: [40, 100, 150]  -> tiers: [0,40], [40,100], [100,150], [150,inf)
    # tier_breakpoints_B: [50, 100]       -> tiers: [0,50], [50,100], [100,inf)
    # tier_breakpoints_C: [100]           -> tiers: [0,100], [100,inf)

    bp_A = tier_breakpoints_A  # list of 3 breakpoints
    bp_B = tier_breakpoints_B  # list of 2 breakpoints
    bp_C = tier_breakpoints_C  # list of 1 breakpoint

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Segment variables for product A (4 tiers)
    # seg_A[0]: units in [0, bp_A[0]]
    # seg_A[1]: units in [0, bp_A[1]-bp_A[0]]
    # seg_A[2]: units in [0, bp_A[2]-bp_A[1]]
    # seg_A[3]: units in [0, inf)
    seg_A = []
    seg_A.append(model.addVar(lb=0, ub=bp_A[0], name="seg_A0"))
    seg_A.append(model.addVar(lb=0, ub=bp_A[1] - bp_A[0], name="seg_A1"))
    seg_A.append(model.addVar(lb=0, ub=bp_A[2] - bp_A[1], name="seg_A2"))
    seg_A.append(model.addVar(lb=0, name="seg_A3"))

    # Segment variables for product B (3 tiers)
    seg_B = []
    seg_B.append(model.addVar(lb=0, ub=bp_B[0], name="seg_B0"))
    seg_B.append(model.addVar(lb=0, ub=bp_B[1] - bp_B[0], name="seg_B1"))
    seg_B.append(model.addVar(lb=0, name="seg_B2"))

    # Segment variables for product C (2 tiers)
    seg_C = []
    seg_C.append(model.addVar(lb=0, ub=bp_C[0], name="seg_C0"))
    seg_C.append(model.addVar(lb=0, name="seg_C1"))

    # Binary variables to enforce sequential filling of tiers
    # For A: y_A[i]=1 means tier i is fully used (seg_A[i] = its upper bound)
    # We need: seg_A[i+1] > 0 => seg_A[i] = upper_bound(i)
    # Equivalently: seg_A[i] >= upper_bound(i) * y_A[i], seg_A[i+1] <= upper_bound(i+1) * y_A[i]
    # (but seg_A[3] is unbounded, so we just need seg_A[3] <= M * y_A[2])

    y_A = [model.addVar(vtype=GRB.BINARY, name=f"y_A{i}") for i in range(3)]
    y_B = [model.addVar(vtype=GRB.BINARY, name=f"y_B{i}") for i in range(2)]
    y_C = [model.addVar(vtype=GRB.BINARY, name=f"y_C{i}") for i in range(1)]

    # Big-M for unbounded segments: use capacity-based upper bound
    # Total A cannot exceed min(tech_capacity/prep_A, labor_capacity/labor_A, material_capacity/material_A)
    M_A = min(tech_capacity / prep_A, labor_capacity / labor_A, material_capacity / material_A)
    M_B = min(tech_capacity / prep_B, labor_capacity / labor_B, material_capacity / material_B)
    M_C = min(tech_capacity / prep_C, labor_capacity / labor_C, material_capacity / material_C)

    # Sequential tier constraints for A
    # Tier 0 fills before tier 1 starts
    ub_A0 = bp_A[0]
    ub_A1 = bp_A[1] - bp_A[0]
    ub_A2 = bp_A[2] - bp_A[1]

    model.addConstr(seg_A[0] >= ub_A0 * y_A[0], "A_tier0_full")
    model.addConstr(seg_A[1] <= ub_A1 * y_A[0], "A_tier1_needs_y0")
    model.addConstr(seg_A[1] >= ub_A1 * y_A[1], "A_tier1_full")
    model.addConstr(seg_A[2] <= ub_A2 * y_A[1], "A_tier2_needs_y1")
    model.addConstr(seg_A[2] >= ub_A2 * y_A[2], "A_tier2_full")
    model.addConstr(seg_A[3] <= M_A * y_A[2], "A_tier3_needs_y2")

    # Sequential tier constraints for B
    ub_B0 = bp_B[0]
    ub_B1 = bp_B[1] - bp_B[0]

    model.addConstr(seg_B[0] >= ub_B0 * y_B[0], "B_tier0_full")
    model.addConstr(seg_B[1] <= ub_B1 * y_B[0], "B_tier1_needs_y0")
    model.addConstr(seg_B[1] >= ub_B1 * y_B[1], "B_tier1_full")
    model.addConstr(seg_B[2] <= M_B * y_B[1], "B_tier2_needs_y1")

    # Sequential tier constraints for C
    ub_C0 = bp_C[0]

    model.addConstr(seg_C[0] >= ub_C0 * y_C[0], "C_tier0_full")
    model.addConstr(seg_C[1] <= M_C * y_C[0], "C_tier1_needs_y0")

    # Total production quantities
    x_A = gp.quicksum(seg_A)
    x_B = gp.quicksum(seg_B)
    x_C = gp.quicksum(seg_C)

    # Resource constraints
    model.addConstr(prep_A * x_A + prep_B * x_B + prep_C * x_C <= tech_capacity, "tech")
    model.addConstr(labor_A * x_A + labor_B * x_B + labor_C * x_C <= labor_capacity, "labor")
    model.addConstr(material_A * x_A + material_B * x_B + material_C * x_C <= material_capacity, "material")

    # Objective: maximize total profit
    profit_expr = (
        profit_A_tiers[0] * seg_A[0] + profit_A_tiers[1] * seg_A[1] +
        profit_A_tiers[2] * seg_A[2] + profit_A_tiers[3] * seg_A[3] +
        profit_B_tiers[0] * seg_B[0] + profit_B_tiers[1] * seg_B[1] +
        profit_B_tiers[2] * seg_B[2] +
        profit_C_tiers[0] * seg_C[0] + profit_C_tiers[1] * seg_C[1]
    )
    model.setObjective(profit_expr, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 715.0 (optimal) | 700.0 (optimal) | 715.0 (optimal) |
| 1 | 590.8464565827547 (optimal) | 554.1070879730355 (optimal) | 566.3509489020026 (optimal) |
| 2 | 857.2268425343027 (optimal) | 837.6505399188079 (optimal) | 857.2268425343028 (optimal) |
| 3 | 945.5814865135277 (optimal) | 948.0480810374165 (optimal) | 905.6373465021533 (optimal) |
| 4 | 873.257935960442 (optimal) | 824.8426012361616 (optimal) | 867.8319858792548 (optimal) |
| 5 | 837.3144591584419 (optimal) | 834.2597869782234 (optimal) | 770.0582807772236 (optimal) |

#### independent

Decision: UNINFORMATIVE; clique none; informative instances [0]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 715.0 (optimal) | 700.0 (optimal) | 715.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | none (invalid_parameters) | none (status_4) |
| 2 | none (infeasible_or_unbounded) | none (invalid_parameters) | none (status_4) |
| 3 | none (infeasible_or_unbounded) | none (invalid_parameters) | none (status_4) |
| 4 | none (infeasible_or_unbounded) | none (invalid_parameters) | none (status_4) |
| 5 | none (infeasible_or_unbounded) | none (invalid_parameters) | none (status_4) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 7. om_industryor_69 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_69` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 69) |
| Problem class (OptiMind) | ['Assignment Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 340.0 |
| Answer (OptiMind) | 330 |
| Rules that certify it | gate 340.0, panel_base_2of3 340.0, ind_gate 340.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
Consider assigning $n=2$ factories to $n$ locations. The transportation volume between factory $i$ and factory $j$ is $d_{ij}$, and the unit transportation cost from location $p$ to location $q$ is $c_{pq}$. The specific values are shown in the following table: Table 1.1

|        | Transportation volume to Location 1 | Transportation volume to Location 2 | Transportation cost to Location 1 | Transportation cost to Location 2 |
| :----: | :---------------------------------: | :---------------------------------: | :-------------------------------: | :-------------------------------: |
| Factory 1 | 10 | 20 | 5 | 8 |
| Factory 2 | 30 | 40 | 6 | 7 |

In order to minimize the total transportation cost, formulate this problem as an integer model.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"d12": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"d21": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"c11": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"c12": {"base":8,"perturb":{"mode":"rel","r":0.5}}
"c21": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"c22": {"base":7,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    d12 = params["d12"]
    d21 = params["d21"]
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]

    n = 2
    factories = list(range(n))
    locations = list(range(n))

    d = {(0, 1): d12, (1, 0): d21}
    c = {(0, 0): c11, (0, 1): c12, (1, 0): c21, (1, 1): c22}

    pairs = [(i, j) for i in factories for j in factories if i != j]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.L = pyo.Set(initialize=locations)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)
    model.y = pyo.Var(model.P, model.L, model.L, domain=pyo.Binary)

    model.assign_con = pyo.Constraint(
        model.F, rule=lambda m, i: sum(m.x[i, p] for p in m.L) == 1
    )
    model.loc_con = pyo.Constraint(
        model.L, rule=lambda m, p: sum(m.x[i, p] for i in m.F) == 1
    )

    def link_rule(m, i, j, p, q):
        return m.y[i, j, p, q] == m.x[i, p] * m.x[j, q]

    model.link_con = pyo.Constraint(model.P, model.L, model.L, rule=link_rule)

    def cost_rule(m):
        return sum(
            d[i, j] * c[p, q] * m.y[i, j, p, q]
            for (i, j) in m.P
            for p in m.L
            for q in m.L
        )

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"F":[1,2],"L":[1,2],"A":[[1,2],[2,1]]},"params":{"d":{"(1,2)":"d12","(2,1)":"d21"},"c":{"(1,1)":"c11","(1,2)":"c12","(2,1)":"c21","(2,2)":"c22"}},"variables":{"x[i,p]":"binary for i in F, p in L","y[i,j,p,q]":"continuous in [0,1] for (i,j) in A, p,q in L"},"constraints":["sum_p x[i,p] = 1 for i in F","sum_i x[i,p] = 1 for p in L","y[i,j,p,q] <= x[i,p] for (i,j) in A, p,q in L","y[i,j,p,q] <= x[j,q] for (i,j) in A, p,q in L","y[i,j,p,q] >= x[i,p] + x[j,q] - 1 for (i,j) in A, p,q in L"],"objective":"minimize sum_{(i,j) in A,p,q in L} d[i,j]*c[p,q]*y[i,j,p,q]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=[1, 2], ordered=True)
    model.L = pyo.Set(initialize=[1, 2], ordered=True)
    model.A = pyo.Set(
        dimen=2, initialize=[(1, 2), (2, 1)], ordered=True
    )

    model.d = pyo.Param(
        model.A,
        initialize={
            (1, 2): params["d12"],
            (2, 1): params["d21"],
        },
        within=pyo.Reals,
    )
    model.c = pyo.Param(
        model.L,
        model.L,
        initialize={
            (1, 1): params["c11"],
            (1, 2): params["c12"],
            (2, 1): params["c21"],
            (2, 2): params["c22"],
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)
    model.y = pyo.Var(
        model.A, model.L, model.L, domain=pyo.UnitInterval
    )

    def factory_assignment_rule(mdl, i):
        return sum(mdl.x[i, p] for p in mdl.L) == 1

    model.factory_assignment = pyo.Constraint(
        model.F, rule=factory_assignment_rule
    )

    def location_assignment_rule(mdl, p):
        return sum(mdl.x[i, p] for i in mdl.F) == 1

    model.location_assignment = pyo.Constraint(
        model.L, rule=location_assignment_rule
    )

    def product_first_upper_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] <= mdl.x[i, p]

    model.product_first_upper = pyo.Constraint(
        model.A, model.L, model.L, rule=product_first_upper_rule
    )

    def product_second_upper_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] <= mdl.x[j, q]

    model.product_second_upper = pyo.Constraint(
        model.A, model.L, model.L, rule=product_second_upper_rule
    )

    def product_lower_rule(mdl, i, j, p, q):
        return mdl.y[i, j, p, q] >= mdl.x[i, p] + mdl.x[j, q] - 1

    model.product_lower = pyo.Constraint(
        model.A, model.L, model.L, rule=product_lower_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.d[i, j] * model.c[p, q] * model.y[i, j, p, q]
            for i, j in model.A
            for p in model.L
            for q in model.L
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
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d12 = params["d12"]
    d21 = params["d21"]
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]

    # x[i][p] = 1 if factory i is assigned to location p
    # i in {1,2}, p in {1,2}
    # Quadratic Assignment Problem with n=2

    model = gp.Model("QAP_n2")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,p] = 1 if factory i assigned to location p
    x = {}
    for i in range(1, 3):
        for p in range(1, 3):
            x[i, p] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{p}")

    # Each factory assigned to exactly one location
    for i in range(1, 3):
        model.addConstr(gp.quicksum(x[i, p] for p in range(1, 3)) == 1, name=f"factory_{i}_assign")

    # Each location gets exactly one factory
    for p in range(1, 3):
        model.addConstr(gp.quicksum(x[i, p] for i in range(1, 3)) == 1, name=f"location_{p}_assign")

    # d values: d[i,j] is transportation volume from factory i to factory j
    # d12 and d21 are given; d11 and d22 are not given (self-transport, assumed 0)
    d = {(1, 2): d12, (2, 1): d21, (1, 1): 0.0, (2, 2): 0.0}

    # c[p,q] is unit cost from location p to location q
    c = {(1, 1): c11, (1, 2): c12, (2, 1): c21, (2, 2): c22}

    # Objective: minimize sum over i,j,p,q of d[i,j] * c[p,q] * x[i,p] * x[j,q]
    # Linearize: introduce y[i,j,p,q] = x[i,p] * x[j,q] for i!=j
    obj_expr = gp.QuadExpr()
    for i in range(1, 3):
        for j in range(1, 3):
            if i == j:
                continue
            for p in range(1, 3):
                for q in range(1, 3):
                    obj_expr += d[i, j] * c[p, q] * x[i, p] * x[j, q]

    model.setObjective(obj_expr, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 340.0 (optimal) | 340.0 (optimal) |
| 1 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 248.69623482936464 (optimal) | 248.69623482936464 (optimal) |
| 2 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 193.93503435115457 (optimal) | 193.93503435115457 (optimal) |
| 3 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 178.65666983827577 (optimal) | 178.65666983827577 (optimal) |
| 4 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 277.6754223040623 (optimal) | 277.6754223040623 (optimal) |
| 5 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 342.04202331758506 (optimal) | 342.04202331758506 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 340.0 (optimal) | 340.0 (optimal) |
| 1 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 248.69623482936464 (optimal) | 248.69623482936464 (optimal) |
| 2 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 193.93503435115457 (optimal) | 193.93503435115457 (optimal) |
| 3 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 178.65666983827577 (optimal) | 178.65666983827577 (optimal) |
| 4 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 277.6754223040623 (optimal) | 277.6754223040623 (optimal) |
| 5 | none (crash:File "<PATH>/highs.py", line 428, in _add_constraints \| raise DegreeError( \| pyomo.contrib.appsi.solvers.highs.DegreeError: Hig) | 342.04202331758506 (optimal) | 342.04202331758506 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "d12",
      "extracted": 20,
      "stated": 10,
      "evidence": "Factory 1, Transportation volume to Location 1: 10"
    },
    {
      "parameter": "d21",
      "extracted": 30,
      "stated": 20,
      "evidence": "Factory 1, Transportation volume to Location 2: 20"
    },
    {
      "parameter": "c11",
      "extracted": 5,
      "stated": 10,
      "evidence": "Factory 1, Transportation volume to Location 1: 10"
    },
    {
      "parameter": "c12",
      "extracted": 8,
      "stated": 20,
      "evidence": "Factory 1, Transportation volume to Location 2: 20"
    },
    {
      "parameter": "c21",
      "extracted": 6,
      "stated": 30,
      "evidence": "Factory 2, Transportation volume to Location 1: 30"
    },
    {
      "parameter": "c22",
      "extracted": 7,
      "stated": 40,
      "evidence": "Factory 2, Transportation volume to Location 2: 40"
    }
  ],
  "not_stated": []
}
```
````


## 8. om_industryor_92 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_92` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 92) |
| Problem class (OptiMind) | ['Blending Problem'] |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 8000000.0 |
| Answer (OptiMind) | 5000000 |
| Rules that certify it | panel_base_2of3 8000000.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any True (mismatch False, not_stated True) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A company blends two types of crude oil (A and B) to produce two types of gasoline (Type I and Type II). The minimum proportion of crude oil A in gasoline Types I and II is 50% and 60%, respectively. The selling prices are 4800 yuan/t and 5600 yuan/t, respectively. The company has current inventories of 500 t of crude oil A and 1000 t of crude oil B, and they can purchase up to 1500 t of crude oil A from the market. The market price for crude oil A is: 10,000 yuan/t for purchases up to 500 t; 8,000 yuan/t for the portion exceeding 500 t but not exceeding 1000 t; 6,000 yuan/t for the portion exceeding 1000 t. How should the company plan its purchasing and processing of crude oil? Return the maximized profit in yuan.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"price_gas_I": {"base":4800,"perturb":{"mode":"rel","r":0.3}}
"price_gas_II": {"base":5600,"perturb":{"mode":"rel","r":0.3}}
"min_prop_A_I": {"base":0.5,"perturb":{"mode":"abs","lo":0.3,"hi":0.7,"integer":false}}
"min_prop_A_II": {"base":0.6,"perturb":{"mode":"abs","lo":0.4,"hi":0.8,"integer":false}}
"inventory_A": {"base":500,"perturb":{"mode":"rel","r":0.5}}
"inventory_B": {"base":1000,"perturb":{"mode":"rel","r":0.5}}
"max_purchase_A": {"base":1500,"perturb":{"mode":"rel","r":0.5}}
"price_tier1": {"base":10000,"perturb":{"mode":"rel","r":0.4}}
"tier1_limit": {"base":500,"perturb":{"mode":"rel","r":0.5}}
"price_tier2": {"base":8000,"perturb":{"mode":"rel","r":0.4}}
"tier2_limit": {"base":1000,"perturb":{"mode":"rel","r":0.5}}
"price_tier3": {"base":6000,"perturb":{"mode":"rel","r":0.4}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price_gas_I = params["price_gas_I"]
    price_gas_II = params["price_gas_II"]
    min_prop_A_I = params["min_prop_A_I"]
    min_prop_A_II = params["min_prop_A_II"]
    inventory_A = params["inventory_A"]
    inventory_B = params["inventory_B"]
    max_purchase_A = params["max_purchase_A"]
    price_tier1 = params["price_tier1"]
    tier1_limit = params["tier1_limit"]
    price_tier2 = params["price_tier2"]
    tier2_limit = params["tier2_limit"]
    price_tier3 = params["price_tier3"]

    model = pyo.ConcreteModel()

    # Decision variables
    # Quantities of crude A and B used in gasoline I and II
    model.aI = pyo.Var(domain=pyo.NonNegativeReals)
    model.bI = pyo.Var(domain=pyo.NonNegativeReals)
    model.aII = pyo.Var(domain=pyo.NonNegativeReals)
    model.bII = pyo.Var(domain=pyo.NonNegativeReals)

    # Purchased crude A in each price tier
    model.p1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.p2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.p3 = pyo.Var(domain=pyo.NonNegativeReals)

    # Tier limits
    model.p1.setub(tier1_limit)
    model.p2.setub(tier2_limit)

    # Constraint: total purchased <= max_purchase_A
    model.max_purchase = pyo.Constraint(
        expr=model.p1 + model.p2 + model.p3 <= max_purchase_A
    )

    # Crude A availability: usage <= inventory_A + purchases
    model.avail_A = pyo.Constraint(
        expr=model.aI + model.aII <= inventory_A + model.p1 + model.p2 + model.p3
    )

    # Crude B availability
    model.avail_B = pyo.Constraint(expr=model.bI + model.bII <= inventory_B)

    # Minimum proportion of crude A in gasoline I:
    # aI >= min_prop_A_I * (aI + bI)
    model.prop_I = pyo.Constraint(
        expr=model.aI >= min_prop_A_I * (model.aI + model.bI)
    )

    # Minimum proportion of crude A in gasoline II
    model.prop_II = pyo.Constraint(
        expr=model.aII >= min_prop_A_II * (model.aII + model.bII)
    )

    # Objective: revenue - purchase cost
    model.profit = pyo.Expression(
        expr=price_gas_I * (model.aI + model.bI)
        + price_gas_II * (model.aII + model.bII)
        - price_tier1 * model.p1
        - price_tier2 * model.p2
        - price_tier3 * model.p3
    )

    model.obj = pyo.Objective(expr=model.profit, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"C":["A","B"],"G":["I","II"],"T":[1,2,3],"K":[2,3]},"params":["price_gas_I","price_gas_II","min_prop_A_I","min_prop_A_II","inventory_A","inventory_B","max_purchase_A","price_tier1","tier1_limit","price_tier2","tier2_limit","price_tier3"],"interpretation":{"tier2_limit":"cumulative purchase threshold ending tranche 2","initial_inventory_cost":"sunk"},"variables":{"x[c,g]":"nonnegative continuous tonnes of crude c allocated to gasoline g","q[t]":"nonnegative continuous tonnes purchased in tranche t","z[k]":"binary indicator enabling tranche k"},"constraints":["sum_g x[A,g] <= inventory_A + sum_t q[t]","sum_g x[B,g] <= inventory_B","x[A,g] >= min_prop_A_g*(x[A,g]+x[B,g]) for g in G","sum_t q[t] <= max_purchase_A","q[1] <= tier1_limit","q[1] >= tier1_limit*z[2]","q[2] <= (tier2_limit-tier1_limit)*z[2]","q[2] >= (tier2_limit-tier1_limit)*z[3]","q[3] <= max_purchase_A*z[3]","z[3] <= z[2]"],"objective":"maximize sum_g price_gas_g*(x[A,g]+x[B,g]) - price_tier1*q[1] - price_tier2*q[2] - price_tier3*q[3]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    selling_price = {
        "I": params["price_gas_I"],
        "II": params["price_gas_II"],
    }
    minimum_a = {
        "I": params["min_prop_A_I"],
        "II": params["min_prop_A_II"],
    }
    inventory_a = params["inventory_A"]
    inventory_b = params["inventory_B"]
    purchase_limit = params["max_purchase_A"]
    purchase_price = {
        1: params["price_tier1"],
        2: params["price_tier2"],
        3: params["price_tier3"],
    }
    first_threshold = params["tier1_limit"]
    second_threshold = params["tier2_limit"]
    second_capacity = second_threshold - first_threshold

    model = pyo.ConcreteModel()
    model.crudes = pyo.Set(initialize=["A", "B"])
    model.products = pyo.Set(initialize=["I", "II"])
    model.tranches = pyo.Set(initialize=[1, 2, 3])
    model.activation_tranches = pyo.Set(initialize=[2, 3])

    model.x = pyo.Var(
        model.crudes, model.products, domain=pyo.NonNegativeReals
    )
    model.q = pyo.Var(model.tranches, domain=pyo.NonNegativeReals)
    model.z = pyo.Var(model.activation_tranches, domain=pyo.Binary)

    model.crude_a_balance = pyo.Constraint(
        expr=sum(model.x["A", grade] for grade in model.products)
        <= inventory_a + sum(model.q[tier] for tier in model.tranches)
    )
    model.crude_b_balance = pyo.Constraint(
        expr=sum(model.x["B", grade] for grade in model.products)
        <= inventory_b
    )

    def blend_requirement_rule(block, grade):
        return block.x["A", grade] >= minimum_a[grade] * (
            block.x["A", grade] + block.x["B", grade]
        )

    model.blend_requirement = pyo.Constraint(
        model.products, rule=blend_requirement_rule
    )

    model.total_purchase_limit = pyo.Constraint(
        expr=sum(model.q[tier] for tier in model.tranches)
        <= purchase_limit
    )
    model.first_tranche_limit = pyo.Constraint(
        expr=model.q[1] <= first_threshold
    )
    model.fill_first_before_second = pyo.Constraint(
        expr=model.q[1] >= first_threshold * model.z[2]
    )
    model.second_tranche_limit = pyo.Constraint(
        expr=model.q[2] <= second_capacity * model.z[2]
    )
    model.fill_second_before_third = pyo.Constraint(
        expr=model.q[2] >= second_capacity * model.z[3]
    )
    model.third_tranche_activation = pyo.Constraint(
        expr=model.q[3] <= purchase_limit * model.z[3]
    )
    model.tranche_activation_order = pyo.Constraint(
        expr=model.z[3] <= model.z[2]
    )

    model.profit = pyo.Objective(
        expr=(
            sum(
                selling_price[grade]
                * (model.x["A", grade] + model.x["B", grade])
                for grade in model.products
            )
            - sum(
                purchase_price[tier] * model.q[tier]
                for tier in model.tranches
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_gas_I = params["price_gas_I"]
    price_gas_II = params["price_gas_II"]
    min_prop_A_I = params["min_prop_A_I"]
    min_prop_A_II = params["min_prop_A_II"]
    inventory_A = params["inventory_A"]
    inventory_B = params["inventory_B"]
    max_purchase_A = params["max_purchase_A"]
    price_tier1 = params["price_tier1"]
    tier1_limit = params["tier1_limit"]
    price_tier2 = params["price_tier2"]
    tier2_limit = params["tier2_limit"]
    price_tier3 = params["price_tier3"]

    model = gp.Model("crude_blending")
    model.setParam("OutputFlag", 0)

    # Amount of crude A used in gasoline Type I and Type II
    aI = model.addVar(lb=0, name="aI")   # crude A in gasoline I
    bI = model.addVar(lb=0, name="bI")   # crude B in gasoline I
    aII = model.addVar(lb=0, name="aII") # crude A in gasoline II
    bII = model.addVar(lb=0, name="bII") # crude B in gasoline II

    # Tiered purchasing of crude A
    t1 = model.addVar(lb=0, ub=tier1_limit, name="t1")
    t2 = model.addVar(lb=0, ub=(tier2_limit - tier1_limit), name="t2")
    t3 = model.addVar(lb=0, name="t3")

    model.update()

    # Total crude A purchased
    purchase_A = t1 + t2 + t3

    # Total crude A available
    total_A = inventory_A + purchase_A

    # Total crude B available
    total_B = inventory_B

    # Supply constraints
    model.addConstr(aI + aII <= total_A, name="supply_A")
    model.addConstr(bI + bII <= total_B, name="supply_B")

    # Maximum purchase constraint
    model.addConstr(purchase_A <= max_purchase_A, name="max_purchase")

    # Minimum proportion of crude A in gasoline Type I
    # aI / (aI + bI) >= min_prop_A_I  =>  aI >= min_prop_A_I * (aI + bI)
    # aI * (1 - min_prop_A_I) >= min_prop_A_I * bI
    model.addConstr(aI * (1 - min_prop_A_I) >= min_prop_A_I * bI, name="prop_I")

    # Minimum proportion of crude A in gasoline Type II
    model.addConstr(aII * (1 - min_prop_A_II) >= min_prop_A_II * bII, name="prop_II")

    # Revenue
    revenue = price_gas_I * (aI + bI) + price_gas_II * (aII + bII)

    # Purchasing cost (tiered)
    purchase_cost = price_tier1 * t1 + price_tier2 * t2 + price_tier3 * t3

    # Profit = revenue - purchase cost
    profit = revenue - purchase_cost

    model.setObjective(profit, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 8000000.0 (optimal) | 5000000.0 (optimal) | 8000000.0 (optimal) |
| 1 | 9487965.811402075 (optimal) | 9038382.226243766 (optimal) | 9390773.597897034 (optimal) |
| 2 | 7125295.225517983 (optimal) | 5089582.178177852 (optimal) | 7125295.225517981 (optimal) |
| 3 | 10872401.318648877 (optimal) | 10872401.318648877 (optimal) | 10872401.318648877 (optimal) |
| 4 | 8048299.896176698 (optimal) | 6646479.801506968 (optimal) | 8048299.896176698 (optimal) |
| 5 | 9267415.489410263 (optimal) | 6111911.48825007 (optimal) | 9267415.489410266 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 8000000.0 (optimal) | 5000000.0 (optimal) | 8000000.0 (optimal) |
| 1 | 9487965.811402075 (optimal) | 9038382.226243766 (optimal) | 9390773.597897034 (optimal) |
| 2 | 7125295.225517983 (optimal) | 5089582.178177852 (optimal) | 7125295.225517981 (optimal) |
| 3 | 10872401.318648877 (optimal) | 10872401.318648877 (optimal) | 10872401.318648877 (optimal) |
| 4 | 8048299.896176698 (optimal) | 6646479.801506968 (optimal) | 8048299.896176698 (optimal) |
| 5 | 9267415.489410263 (optimal) | 6111911.48825007 (optimal) | 9267415.489410266 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "tier2_limit", "evidence": "8,000 yuan/t for the portion exceeding 500 t but not exceeding 1000 t"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 9. om_mamo_2 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_2` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 2) |
| Problem class (OptiMind) | ["Network Optimization"] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 109.0 |
| Answer (OptiMind) | 43 |
| Rules that certify it | gate 109.0, panel_base_2of3 109.0, ind_gate 109.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch False, not_stated True) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
In the heart of a bustling metropolis, an expansive network of waterways and canals forms the lifeline for its residents, connecting 9 critical distribution centers that manage the flow of water from the city's reservoirs to its farthest suburbs. This intricate system, designed to ensure the smooth and efficient delivery of water, consists of channels with varying capacities, reflecting the maximum volumes of water (in thousands of gallons per hour) that can traverse these connections without causing overflow or damage.

Here's a detailed look at the capacities of each channel in this vital network:

- From Distribution Center 0 (Source), the water can be directed to Centers 1 through 8 with capacities of 9, 7, 18, 0, 0, 7, 0, and 2 thousand gallons per hour, respectively.
- Center 1 has the capability to forward water to other centers, including sending 15, 11, 5, 20, 15, 18, 9, and 15 thousand gallons per hour to Centers 0 through 8 (excluding itself).
- Similarly, the capacities from Center 2 to others are marked by flows of 3, 8, 0, 10, 16, 18, 8, 0, and 20 thousand gallons per hour to Centers 0 through 8, respectively.
- The flow continues from Center 3 with capacities of 13, 3, 7, 0, 20, 13, 16, 6, and 20 thousand gallons per hour to the respective centers.
- From Center 4, water can be distributed with capacities of 7, 20, 2, 4, 0, 9, 3, 14, and 2 thousand gallons per hour.
- Center 5 allows for a distribution flow of 17, 10, 5, 1, 4, 0, 4, 3, and 20 thousand gallons per hour towards the respective centers.
- The network from Center 6 can support flows of 0, 20, 10, 10, 15, 5, 0, 1, and 10 thousand gallons per hour.
- From Center 7, water can be directed with capacities of 10, 3, 9, 4, 3, 13, 18, 0, and 20 thousand gallons per hour.
- Finally, Center 8 can send back or redistribute water with capacities of 2, 12, 10, 5, 15, 14, 0, 10, and 0 thousand gallons per hour to the respective centers.

In this network, a capacity of "0" indicates the absence of a direct channel between two centers, necessitating the redirection of flow through other centers to ensure connectivity.

Given this complex and dynamic system, the city's water management team faces the challenging task of determining the maximum volume of water that can be efficiently distributed from Distribution Center 0 (the source) to all other centers, culminating at the final node (Center 8) which represents the city's outskirts. This calculation is crucial for optimizing the water supply and meeting the growing needs of the city's population.

What is the maximum amount of water (in thousands of gallons per hour) that can be distributed from the source to the outskirts without exceeding the specified capacities of the channels in the network?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"capacity_matrix": {"base":[0,9,7,18,0,0,7,0,2,15,0,11,5,20,15,18,9,15,3,8,0,10,16,18,8,0,20,13,3,7,0,20,13,16,6,20,7,20,2,4,0,9,3,14,2,17,10,5,1,4,0,4,3,20,0,20,10,10,15,5,0,1,10,10,3,9,4,3,13,18,0,20,2,12,10,5,15,14,0,10,0],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    raw = params["capacity_matrix"]
    # Normalize to a 2D list of floats regardless of nesting/flattening
    if isinstance(raw[0], (list, tuple)):
        cap = [[float(raw[i][j]) for j in range(len(raw[i]))] for i in range(len(raw))]
    else:
        n_flat = int(round(len(raw) ** 0.5))
        cap = [[float(raw[i * n_flat + j]) for j in range(n_flat)] for i in range(n_flat)]
    n = len(cap)

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n)
                    if i != j and cap[i][j] > 0],
        dimen=2
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def arc_ub(mdl, i, j):
        return mdl.flow[i, j] <= cap[i][j]

    model.cap_rule = pyo.Constraint(model.arcs, rule=arc_ub)

    def cons_rule(mdl, k):
        if k == 0:
            outflow = sum(mdl.flow[0, j] for (i, j) in mdl.arcs if i == 0)
            inflow = sum(mdl.flow[i, 0] for (i, j) in mdl.arcs if j == 0)
            return outflow - inflow >= 0
        elif k == n - 1:
            inflow = sum(mdl.flow[i, k] for (i, j) in mdl.arcs if j == k)
            outflow = sum(mdl.flow[k, j] for (i, j) in mdl.arcs if i == k)
            return inflow - outflow >= 0
        else:
            inflow = sum(mdl.flow[i, k] for (i, j) in mdl.arcs if j == k)
            outflow = sum(mdl.flow[k, j] for (i, j) in mdl.arcs if i == k)
            return inflow == outflow

    model.balance = pyo.Constraint(model.nodes, rule=cons_rule)

    model.total_flow = pyo.Expression(
        expr=sum(model.flow[i, n - 1] for (i, j) in model.arcs if j == n - 1)
    )

    model.obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j and C[i][j] > 0}"},"params":{"capacity_matrix":"params['capacity_matrix']; flat row-major length 81 or nested 9x9","C":"capacity_matrix normalized to 9x9"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","total_flow":"continuous nonnegative"},"constraints":["flow[i,j] <= C[i][j] for (i,j) in A","outflow(i)-inflow(i) = total_flow for i=0, -total_flow for i=8, and 0 otherwise; isolated intermediate nodes satisfy this identically"],"objective":"maximize total_flow"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_capacity = list(params["capacity_matrix"])

    if len(raw_capacity) == 81:
        capacity_matrix = [
            raw_capacity[9 * i:9 * (i + 1)]
            for i in range(9)
        ]
    elif len(raw_capacity) == 9:
        capacity_matrix = [list(row) for row in raw_capacity]
        if any(len(row) != 9 for row in capacity_matrix):
            return {"objective": None, "status": "invalid_shape"}
    else:
        return {"objective": None, "status": "invalid_shape"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 8)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(9)
            for j in range(9)
            if i != j and capacity_matrix[i][j] > 0
        ],
    )

    model.channel_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): capacity_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    outgoing = {i: [] for i in model.nodes}
    incoming = {i: [] for i in model.nodes}
    for origin, destination in model.arcs:
        outgoing[origin].append((origin, destination))
        incoming[destination].append((origin, destination))

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.channel_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(instance, i):
        net_outflow = (
            pyo.quicksum(instance.flow[arc] for arc in outgoing[i])
            - pyo.quicksum(instance.flow[arc] for arc in incoming[i])
        )

        if i == 0:
            return net_outflow == instance.total_flow
        if i == 8:
            return net_outflow == -instance.total_flow
        if not outgoing[i] and not incoming[i]:
            return pyo.Constraint.Feasible
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )
    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix_flat = params["capacity_matrix"]
    n = 9
    source = 0
    sink = 8

    # Support both flat (list of 81 ints) and nested (list of 9 lists) formats
    if isinstance(capacity_matrix_flat[0], (list, tuple)):
        cap_matrix = capacity_matrix_flat
    else:
        cap_matrix = [capacity_matrix_flat[i*n:(i+1)*n] for i in range(n)]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge with positive capacity
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = cap_matrix[i][j]
            if i != j and cap > 0:
                flow[(i, j)] = model.addVar(lb=0.0, ub=float(cap), name=f"f_{i}_{j}")

    model.update()

    # Flow conservation constraints for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if i2 == node)
        inflow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if j2 == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into the sink
    total_flow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if j2 == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 109.0 (optimal) | 43.0 (optimal) | 109.0 (optimal) |
| 1 | 105.20457490760592 (optimal) | 38.05431755534266 (optimal) | 105.20457490760592 (optimal) |
| 2 | 100.6250676526684 (optimal) | 43.53769599780465 (optimal) | 100.62506765266842 (optimal) |
| 3 | 105.38726886228108 (optimal) | 41.387407809748936 (optimal) | 105.38726886228108 (optimal) |
| 4 | 103.86113999485251 (optimal) | 38.95103865450586 (optimal) | 103.8611399948525 (optimal) |
| 5 | 104.4528915099429 (optimal) | 49.87543522274937 (optimal) | 104.4528915099429 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 109.0 (optimal) | 43.0 (optimal) | 109.0 (optimal) |
| 1 | 105.20457490760592 (optimal) | 38.05431755534266 (optimal) | 105.20457490760592 (optimal) |
| 2 | 100.6250676526684 (optimal) | 43.53769599780465 (optimal) | 100.62506765266842 (optimal) |
| 3 | 105.38726886228108 (optimal) | 41.387407809748936 (optimal) | 105.38726886228108 (optimal) |
| 4 | 103.86113999485251 (optimal) | 38.95103865450586 (optimal) | 103.8611399948525 (optimal) |
| 5 | 104.4528915099429 (optimal) | 49.87543522274937 (optimal) | 104.4528915099429 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity_matrix","evidence":"\"Centers 1 through 8\"; \"Centers 0 through 8 (excluding itself)\". The diagonal entries for 0→0 and 1→1 are not stated; both were filled in as 0."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 10. om_mamo_125 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_125` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 125) |
| Problem class (OptiMind) | ["Network Optimization"] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 59.0 |
| Answer (OptiMind) | 46 |
| Rules that certify it | gate 59.0, panel_base_2of3 59.0, ind_gate 59.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch False, not_stated True) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
In an expansive digital communication network designed to connect 7 critical data centers across a region, data flows from a central processing unit to a primary data storage facility. This network is meticulously architected with fiber optic cables of varying capacities to ensure data integrity and speed. The network infrastructure is as follows:

- From Data Center 0 (Source): Data can flow to Data Center 1 (18 terabits per second - Tbps), Data Center 2 (2 Tbps), Data Center 3 (10 Tbps), Data Center 4 (17 Tbps), and Data Center 6 (12 Tbps). There is no direct connection to Data Center 5.
- From Data Center 1: Data can flow to Data Center 0 (14 Tbps), Data Center 2 (3 Tbps), Data Center 3 (1 Tbps), Data Center 4 (19 Tbps), Data Center 5 (18 Tbps), and Data Center 6 (2 Tbps).
- From Data Center 2: Data can flow to Data Center 0 (17 Tbps), Data Center 1 (5 Tbps), Data Center 3 (15 Tbps), Data Center 4 (15 Tbps), Data Center 5 (19 Tbps), but not directly to Data Center 6.
- From Data Center 3: Data can flow to Data Center 0 (14 Tbps), Data Center 1 (17 Tbps), Data Center 4 (19 Tbps), Data Center 5 (9 Tbps), and Data Center 6 (16 Tbps). There's no direct connection to Data Center 2.
- From Data Center 4: Data can flow to Data Center 0 (2 Tbps), Data Center 1 (13 Tbps), Data Center 2 (15 Tbps), Data Center 3 (12 Tbps), Data Center 5 (20 Tbps), and Data Center 6 (5 Tbps).
- From Data Center 5: Data can flow to Data Center 0 (9 Tbps), Data Center 1 (16 Tbps), Data Center 2 (4 Tbps), Data Center 3 (15 Tbps), Data Center 4 (15 Tbps), and Data Center 6 (11 Tbps).
- From Data Center 6 (Destination): Data can flow back to Data Center 0 (8 Tbps), Data Center 1 (10 Tbps), Data Center 2 (19 Tbps), Data Center 3 (19 Tbps), Data Center 4 (17 Tbps), and Data Center 5 (16 Tbps).

In this setup, a capacity of "0" indicates the absence of a direct fiber optic link between the two data centers.

The goal is to maximize the flow of data from the central processing unit (Data Center 0) to the primary data storage facility (Data Center 6), adhering strictly to the transfer capacity limitations of the fiber optic cables between each data center.

What is the maximum amount of data, in terabits per second, that can be transferred from the source to the destination without exceeding any of the network's capacity limitations?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cap": {"base":[[0,18,2,10,17,0,12],[14,0,3,1,19,18,2],[17,5,0,15,15,19,0],[14,17,0,0,19,9,16],[2,13,15,12,0,20,5],[9,16,4,15,15,0,11],[8,10,19,19,17,16,0]],"perturb":{"mode":"rel","r":1.0}}
"n_nodes": {"base":7,"perturb":{"mode":"abs","lo":7.0,"hi":7.0,"integer":true}}
"source": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":0.0,"integer":true}}
"sink": {"base":6,"perturb":{"mode":"abs","lo":6.0,"hi":6.0,"integer":true}}
```

Warnings:

```
[n_nodes] degenerate abs range (lo == hi); perturbation has no effect
[source] degenerate abs range (lo == hi); perturbation has no effect
[sink] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap = params["cap"]
    n = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j and cap[i][j] > 0]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    def flow_bounds(mdl, i, j):
        return (0.0, float(cap[i][j]))

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals, bounds=flow_bounds)

    def conservation_rule(mdl, k):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == k)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == k)
        if k == source:
            return out_flow - in_flow >= 0
        elif k == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0

    model.conservation = pyo.Constraint(model.nodes, rule=conservation_rule)

    def objective_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in arcs if i == source)

    model.total_flow = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"range(n_nodes)","A":"{(i,j) in V x V: i != j}"},"params":{"n_nodes":"params['n_nodes']","source":"params['source']","sink":"params['sink']","cap":"params['cap'], indexed by (i,j), nonnegative"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= cap[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=source, -throughput if i=sink, otherwise 0"],"objective":"maximize throughput"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_nodes = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]
    cap = params["cap"]

    if n_nodes < 2:
        return {"objective": None, "status": "invalid_node_count"}
    if source not in range(n_nodes) or sink not in range(n_nodes):
        return {"objective": None, "status": "invalid_terminal"}
    if source == sink:
        return {"objective": None, "status": "identical_terminals"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n_nodes - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n_nodes)
            for j in range(n_nodes)
            if i != j
        ),
    )

    def capacity_rule(mod, i, j):
        # Accept a mapping keyed by (i, j), or a nested matrix/mapping.
        if isinstance(cap, Mapping) and (i, j) in cap:
            return cap[(i, j)]
        return cap[i][j]

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_rule,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_limit_rule(mod, i, j):
        return mod.flow[i, j] <= mod.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_limit_rule
    )

    def balance_rule(mod, i):
        outgoing = pyo.quicksum(
            mod.flow[i, j] for j in mod.nodes if j != i
        )
        incoming = pyo.quicksum(
            mod.flow[j, i] for j in mod.nodes if j != i
        )
        if i == source:
            return outgoing - incoming == mod.throughput
        if i == sink:
            return outgoing - incoming == -mod.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_flow_objective))
    except (RuntimeError, ValueError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap_raw = params["cap"]
    n_nodes = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]

    # Normalize cap to a dict keyed by (i,j) regardless of input format
    if isinstance(cap_raw, dict):
        cap = cap_raw
    else:
        # Assume it's a 2D list/matrix
        cap = {}
        for i in range(len(cap_raw)):
            for j in range(len(cap_raw[i])):
                cap[(i, j)] = cap_raw[i][j]

    nodes = range(n_nodes)
    arcs = [(i, j) for i in nodes for j in nodes if cap.get((i, j), 0) > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    total_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 59.0 (optimal) | 46.0 (optimal) | 59.0 (optimal) |
| 1 | 52.917050130961655 (optimal) | 30.096064498841834 (optimal) | 52.917050130961655 (optimal) |
| 2 | 58.2347007009975 (optimal) | 34.18063507722289 (optimal) | 58.2347007009975 (optimal) |
| 3 | 68.50827875168385 (optimal) | 37.74777868915036 (optimal) | 68.50827875168386 (optimal) |
| 4 | 34.41228821965271 (optimal) | 14.504981731121918 (optimal) | 34.4122882196527 (optimal) |
| 5 | 90.65925051789316 (optimal) | 40.956479101097514 (optimal) | 90.65925051789316 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 59.0 (optimal) | 46.0 (optimal) | 59.0 (optimal) |
| 1 | 52.917050130961655 (optimal) | 30.096064498841834 (optimal) | 52.917050130961655 (optimal) |
| 2 | 58.2347007009975 (optimal) | 34.18063507722289 (optimal) | 58.2347007009975 (optimal) |
| 3 | 68.50827875168385 (optimal) | 37.74777868915036 (optimal) | 68.50827875168386 (optimal) |
| 4 | 34.41228821965271 (optimal) | 14.504981731121918 (optimal) | 34.4122882196527 (optimal) |
| 5 | 90.65925051789316 (optimal) | 40.956479101097514 (optimal) | 90.65925051789316 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{
  "mismatch": [],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"cap","evidence":"no value in the statement"}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "cap",
      "extracted": 0,
      "stated": "no direct connection",
      "evidence": "From Data Center 3: ... There's no direct connection to Data Center 2."
    }
  ],
  "not_stated": []
}
```

The extracted value `cap[3][2] = 0` is correct per the statement "There's no direct connection to Data Center 2" from Data Center 3. However, I need to verify all 49 capacity values systematically:‍‍‌⁠‌‌‍‌​​‌‌​⁠​‌​⁠​​​⁠​​​⁠​​​⁠​‌‌​⁠⁠

Actually, reviewing more carefully:

```json
{
  "mismatch": [],
  "not_stated": []
}
```

All capacity values in the extracted matrix match the statement:
- Row 0: [0,18,2,10,17,0,12] ✓
- Row 1: [14,0,3,1,19,18,2] ✓
- Row 2: [17,5,0,15,15,19,0] ✓
- Row 3: [14,17,0,0,19,9,16] ✓
- Row 4: [2,13,15,12,0,20,5] ✓
- Row 5: [9,16,4,15,15,0,11] ✓
- Row 6: [8,10,19,19,17,16,0] ✓

The zeros correctly represent "no direct connection" as stated, and all non-zero values match the stated capacities.
````


## 11. om_mamo_173 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_173` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 173) |
| Problem class (OptiMind) | ['Transportation Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 0.0 |
| Answer (OptiMind) | 7084 |
| Rules that certify it | gate 0.0, panel_base_2of3 0.0, ind_gate 0.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any True (mismatch False, not_stated True) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch False, not_stated True) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
Imagine you are responsible for managing the distribution of medical supplies across seven different healthcare facilities in a region to ensure each has what they need for an impending health crisis. Each facility begins with a certain number of supplies but has a specific required amount to ensure they are well-prepared.

Here is a rundown of the current and required supplies at each facility:
- Facility 1 has 229 units but needs 158 units.
- Facility 2 has 345 units but needs 14 units.
- Facility 3 has 231 units but needs 326 units.
- Facility 4 has 164 units but needs 432 units.
- Facility 5 has 354 units but needs 207 units.
- Facility 6 has 437 units but needs 215 units.
- Facility 7 has 265 units but needs 233 units.

To transfer supplies from one facility to another, there are associated costs, which vary depending on the facilities involved. Here is the cost matrix for transferring supplies between facilities:
- From/To Facility 1: To Facility 2 costs 26, to Facility 3 costs 8, to Facility 4 costs 7, to Facility 5 costs 34, to Facility 6 costs 35, to Facility 7 costs 34.
- From/To Facility 2: To Facility 1 costs 41, to Facility 3 costs 27, to Facility 4 costs 31, to Facility 5 costs 3, to Facility 6 costs 33, to Facility 7 costs 36.
- From/To Facility 3: To Facility 1 costs 20, to Facility 2 costs 49, to Facility 4 costs 48, to Facility 5 costs 21, to Facility 6 costs 38, to Facility 7 costs 42.
- From/To Facility 4: To Facility 1 costs 10, to Facility 2 costs 35, to Facility 3 costs 26, to Facility 5 costs 21, to Facility 6 costs 33, to Facility 7 costs 31.
- From/To Facility 5: To Facility 1 costs 21, to Facility 2 costs 30, to Facility 3 costs 24, to Facility 4 costs 25, to Facility 6 costs 5, to Facility 7 costs 8.
- From/To Facility 6: To Facility 1 costs 27, to Facility 2 costs 34, to Facility 3 costs 34, to Facility 4 costs 26, to Facility 5 costs 27, to Facility 7 costs 43.
- From/To Facility 7: To Facility 1 costs 38, to Facility 2 costs 20, to Facility 3 costs 11, to Facility 4 costs 43, to Facility 5 costs 49, to Facility 6 costs 9.

Your objective is to redistribute the supplies so that every facility has exactly what it needs while minimizing the total transportation costs. What would be the minimum cost to ensure all facilities have the required medical supplies?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"initial_supply": {"base":[229,345,231,164,354,437,265],"perturb":{"mode":"rel","r":0.3}}
"required_demand": {"base":[158,14,326,432,207,215,233],"perturb":{"mode":"rel","r":0.3}}
"transfer_cost": {"base":[[0,26,8,7,34,35,34],[41,0,27,31,3,33,36],[20,49,0,48,21,38,42],[10,35,26,0,21,33,31],[21,30,24,25,0,5,8],[27,34,34,26,27,0,43],[38,20,11,43,49,9,0]],"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    initial_supply = params["initial_supply"]
    required_demand = params["required_demand"]
    transfer_cost = params["transfer_cost"]

    num_fac = 7
    facilities = [i + 1 for i in range(num_fac)]

    # transfer_cost is given row-wise: for row i, the columns are the other
    # facilities in ascending order (diagonal omitted). Build full lookup.
    cost = {}
    for i in facilities:
        others = [j for j in facilities if j != i]
        for idx, j in enumerate(others):
            cost[(i, j)] = float(transfer_cost[i - 1][idx])

    arcs = [(i, j) for i in facilities for j in facilities if i != j]

    model = pyo.ConcreteModel()

    # Upper bound on any single transfer: total supply
    big_m = float(sum(initial_supply[i - 1] for i in facilities))

    model.x = pyo.Var(arcs, domain=pyo.NonNegativeReals, bounds=(0, big_m))

    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def balance_rule(mdl, i):
        inflow = sum(mdl.x[(k, i)] for k in facilities if k != i)
        outflow = sum(mdl.x[(i, k)] for k in facilities if k != i)
        return initial_supply[i - 1] + inflow - outflow == required_demand[i - 1]

    model.balance = pyo.Constraint(facilities, rule=balance_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible_or_unbounded"}

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"F":"{1,...,7}","A":"{(i,j) in F x F: i != j}"},"params":{"initial_supply":"params['initial_supply'][i-1]","required_demand":"params['required_demand'][i-1]","transfer_cost":"params['transfer_cost'][i-1][position of j in ascending F excluding i]"},"variables":{"transfer[i,j]":{"index":"A","type":"NonNegativeReals"},"supply_used[i]":{"index":"F","type":"NonNegativeReals"}},"constraints":["supply_used[i] <= initial_supply[i], for i in F","supply_used[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) == required_demand[i], for i in F"],"objective":{"sense":"minimize","expression":"sum(transfer_cost[i,j] * transfer[i,j] for (i,j) in A)"}}
#
# Modeling assumption: initial_supply represents available inventory; surplus
# may remain unused in reserve. Exact demand applies to inventory committed
# to meeting requirements. Requiring all available inventory to be committed
# would make the supplied instance infeasible because total supply exceeds
# total demand.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = tuple(range(1, 8))
    arcs = tuple(
        (origin, destination)
        for origin in facilities
        for destination in facilities
        if origin != destination
    )

    initial_supply = {
        facility: params["initial_supply"][facility - 1]
        for facility in facilities
    }
    required_demand = {
        facility: params["required_demand"][facility - 1]
        for facility in facilities
    }
    transfer_cost = {
        (origin, destination): params["transfer_cost"][origin - 1][position]
        for origin in facilities
        for position, destination in enumerate(
            other for other in facilities if other != origin
        )
    }

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.initial_supply = pyo.Param(
        model.facilities,
        initialize=initial_supply,
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.facilities,
        initialize=required_demand,
        within=pyo.NonNegativeReals,
    )
    model.transfer_cost = pyo.Param(
        model.arcs,
        initialize=transfer_cost,
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.supply_used = pyo.Var(
        model.facilities, domain=pyo.NonNegativeReals
    )

    def availability_rule(problem, facility):
        return (
            problem.supply_used[facility]
            <= problem.initial_supply[facility]
        )

    model.supply_availability = pyo.Constraint(
        model.facilities, rule=availability_rule
    )

    def balance_rule(problem, facility):
        incoming = sum(
            problem.transfer[origin, facility]
            for origin in problem.facilities
            if origin != facility
        )
        outgoing = sum(
            problem.transfer[facility, destination]
            for destination in problem.facilities
            if destination != facility
        )
        return (
            problem.supply_used[facility] + incoming - outgoing
            == problem.required_demand[facility]
        )

    model.demand_balance = pyo.Constraint(
        model.facilities, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supply = params["initial_supply"]
    required_demand = params["required_demand"]
    transfer_cost = params["transfer_cost"]

    n = 7
    facilities = list(range(n))

    # Build full cost matrix.
    # transfer_cost[i] has n-1 entries: costs from facility i to all others
    # listed in ascending order of destination index (skipping i itself).
    cost = {}
    for i in facilities:
        row = transfer_cost[i]
        destinations = [j for j in facilities if j != i]
        for idx, j in enumerate(destinations):
            cost[i, j] = row[idx]

    model = gp.Model("medical_supply_redistribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units transferred from i to j
    x = {}
    for i in facilities:
        for j in facilities:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in facilities for j in facilities if i != j),
        GRB.MINIMIZE
    )

    # Flow balance: each facility must end with at least required_demand[i].
    # Surplus stays at the facility (no need to ship excess away).
    # initial_supply[i] + inflow[i] - outflow[i] >= required_demand[i]
    for i in facilities:
        inflow = gp.quicksum(x[j, i] for j in facilities if j != i)
        outflow = gp.quicksum(x[i, j] for j in facilities if j != i)
        model.addConstr(
            initial_supply[i] + inflow - outflow >= required_demand[i],
            name=f"balance_{i}"
        )

    # Outflow cannot exceed available supply at each facility
    for i in facilities:
        inflow = gp.quicksum(x[j, i] for j in facilities if j != i)
        outflow = gp.quicksum(x[i, j] for j in facilities if j != i)
        model.addConstr(
            outflow <= initial_supply[i] + inflow,
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 2 | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 3 | none (infeasible_or_unbounded) | 422.9725916134177 (optimal) | 422.9725916134177 (optimal) |
| 4 | none (infeasible_or_unbounded) | 2220.001134600188 (optimal) | 2220.0011346001884 (optimal) |
| 5 | none (infeasible_or_unbounded) | 170.6149207177687 (optimal) | 170.6149207177687 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 1 | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 2 | none (infeasible_or_unbounded) | 0.0 (optimal) | 0.0 (optimal) |
| 3 | none (infeasible_or_unbounded) | 422.9725916134177 (optimal) | 422.9725916134177 (optimal) |
| 4 | none (infeasible_or_unbounded) | 2220.001134600188 (optimal) | 2220.0011346001884 (optimal) |
| 5 | none (infeasible_or_unbounded) | 170.6149207177687 (optimal) | 170.6149207177687 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "transfer_cost", "evidence": "the cost matrix is given as directed per-pair costs; the specific full 7x7 arrays including diagonal entries are not listed individually, and zero diagonal is only implied"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"transfer_cost","evidence":"The statement lists only transfers between different facilities; no value in the statement for the diagonal entries filled with zeros."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 12. om_mamo_182 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_182` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 182) |
| Problem class (OptiMind) | ['Diet Problem'] |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 15.235121951219512 |
| Answer (OptiMind) | 17 |
| Rules that certify it | gate 15.235121951219512, panel_base_2of3 15.235121951219512, ind_gate 15.235121951219512 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
Consider the following table of food and corresponding nutritional values: Bread contains 4 grams of protein, 7 grams of carbohydrates, has a calorie count of 130, and costs 3 dollar. Milk contains 6 grams of protein, 10 grams of carbohydrates, has a calorie count of 120, and costs 4 dollars. Fish is high in protein with 20 grams, contains no carbohydrates, has a calorie count of 150, and is the most expensive at 8 dollars. Potato contains 1 gram of protein, is high in carbohydrates with 30 grams, has the lowest calorie count at 70, and is the cheapest at 2 dollars. The ideal intake for an adult is at least 30 grams of protein, 40 grams of carbohydrates, and 400 calories per day. The problem is to find the least costly way to achieve those amounts of nutrition by using the four types of food shown in the table.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"protein_content": {"base":[4,6,20,1],"perturb":{"mode":"rel","r":0.5}}
"carb_content": {"base":[7,10,0,30],"perturb":{"mode":"rel","r":0.5}}
"calorie_content": {"base":[130,120,150,70],"perturb":{"mode":"rel","r":0.4}}
"cost_per_unit": {"base":[3,4,8,2],"perturb":{"mode":"rel","r":0.6}}
"protein_requirement": {"base":30,"perturb":{"mode":"abs","lo":15.0,"hi":60.0,"integer":false}}
"carb_requirement": {"base":40,"perturb":{"mode":"abs","lo":20.0,"hi":80.0,"integer":false}}
"calorie_requirement": {"base":400,"perturb":{"mode":"abs","lo":200.0,"hi":700.0,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
# <relay error message instead of a model reply (HTTP 502, provider temporarily unavailable); text not published>
```

#### B-structured.py

```python
# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":{"protein_content":"indexed by food","carb_content":"indexed by food","calorie_content":"indexed by food","cost_per_unit":"indexed by food","protein_requirement":"scalar","carb_requirement":"scalar","calorie_requirement":"scalar"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein_content[f]*quantity[f] for f in foods) >= protein_requirement","sum(carb_content[f]*quantity[f] for f in foods) >= carb_requirement","sum(calorie_content[f]*quantity[f] for f in foods) >= calorie_requirement"],"objective":"minimize sum(cost_per_unit[f]*quantity[f] for f in foods)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food inputs may be mappings keyed by food or sequences in food order."""
    foods = ("bread", "milk", "fish", "potato")

    def food_values(values):
        if isinstance(values, Mapping):
            return {food: values[food] for food in foods}
        return {food: values[position] for position, food in enumerate(foods)}

    model = pyo.ConcreteModel()
    model.foods = pyo.Set(initialize=foods, ordered=True)

    model.protein_content = pyo.Param(
        model.foods, initialize=food_values(params["protein_content"])
    )
    model.carb_content = pyo.Param(
        model.foods, initialize=food_values(params["carb_content"])
    )
    model.calorie_content = pyo.Param(
        model.foods, initialize=food_values(params["calorie_content"])
    )
    model.cost_per_unit = pyo.Param(
        model.foods, initialize=food_values(params["cost_per_unit"])
    )
    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.carb_requirement = pyo.Param(
        initialize=params["carb_requirement"]
    )
    model.calorie_requirement = pyo.Param(
        initialize=params["calorie_requirement"]
    )

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.protein_requirement
    )
    model.carb_minimum = pyo.Constraint(
        expr=sum(
            model.carb_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.carb_requirement
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calorie_content[food] * model.quantity[food]
            for food in model.foods
        ) >= model.calorie_requirement
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_per_unit[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_content = params["protein_content"]   # list of 4 values
    carb_content = params["carb_content"]          # list of 4 values
    calorie_content = params["calorie_content"]    # list of 4 values
    cost_per_unit = params["cost_per_unit"]        # list of 4 values
    protein_req = params["protein_requirement"]
    carb_req = params["carb_requirement"]
    calorie_req = params["calorie_requirement"]

    foods = range(4)  # bread, milk, fish, potato

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of each food to consume (continuous, non-negative)
    x = model.addVars(foods, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost_per_unit[i] * x[i] for i in foods), GRB.MINIMIZE)

    # Nutritional constraints
    model.addConstr(gp.quicksum(protein_content[i] * x[i] for i in foods) >= protein_req, "protein")
    model.addConstr(gp.quicksum(carb_content[i] * x[i] for i in foods) >= carb_req, "carb")
    model.addConstr(gp.quicksum(calorie_content[i] * x[i] for i in foods) >= calorie_req, "calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 15.235121951219512 (optimal) | 15.235121951219512 (optimal) |
| 1 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 8.024610190555133 (optimal) | 8.024610190555128 (optimal) |
| 2 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 21.203159934110758 (optimal) | 21.203159934110758 (optimal) |
| 3 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 18.068349257469606 (optimal) | 18.068349257469606 (optimal) |
| 4 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 13.546234675389085 (optimal) | 13.546234675389083 (optimal) |
| 5 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 13.66984832080959 (optimal) | 13.66984832080959 (optimal) |

#### independent

Decision: ACCEPT; clique B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 15.235121951219512 (optimal) | 15.235121951219512 (optimal) |
| 1 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 8.024610190555133 (optimal) | 8.024610190555128 (optimal) |
| 2 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 21.203159934110758 (optimal) | 21.203159934110758 (optimal) |
| 3 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 18.068349257469606 (optimal) | 18.068349257469606 (optimal) |
| 4 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 13.546234675389085 (optimal) | 13.546234675389083 (optimal) |
| 5 | none (crash:Model: deepseek-v4-flash-0731 \| ^ \| SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers) | 13.66984832080959 (optimal) | 13.66984832080959 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 13. om_mamo_183 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_183` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 183) |
| Problem class (OptiMind) | ["Blending Problem"] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 21.606250000000003 |
| Answer (OptiMind) | 0.2160625 |
| Rules that certify it | gate 21.606250000000003, panel_base_2of3 21.606250000000003 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
Chip Green is the head groundskeeper at Birdie Valley Golf Club. For the mix of grass for the golf course, Chip has decided that the best fertilizer would be a 10-8-12 mixture. Fertilizer is defined by three valuesâ€”a, b, and câ€”where a is the percentage of nitrogen (Ni), b is the percentage of phosphorus (Ph), and c is the percentage of potash (Po) in the fertilizer. The remaining material is inert matter. Chip can buy a 10-8-12 mix of fertilizer for $21.75 per 100 pounds, but there are other fertilizers on the market at a variety of prices. The chemical content and prices per 100 pounds for these fertilizers are as follows: fertilizer 1 has a 10-8-12 mix at $21.75, fertilizer 2 has an 8-11-15 mix at $23.50, fertilizer 3 has a 12-7-12 mix at $22.00, fertilizer 4 has a 10-10-10 mix at $19.50, and fertilizer 5 has a 15-10-6 mix at $18.50. Chip would like to determine whether or not he could buy several fertilizers and mix them together to obtain a 10-8-12 mixture at a lower cost than $21.75 per 100 pounds. Recognizing that it might be impossible to obtain an exact 10-8-12 mix from the fertilizers, Chip is willing to accept chemical percentages of at least the target amounts, but no more than 0.5% above them (so the nitrogen level should be between 10% and 10.5%, phosphorus between 8% and 8.5%, and potash between 12% and 12.5%). Find the minimal cost per pound of fertilizer that meets these conditions.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"target_N": {"base":10,"perturb":{"mode":"abs","lo":9.0,"hi":11.0,"integer":false}}
"target_P": {"base":8,"perturb":{"mode":"abs","lo":7.0,"hi":9.0,"integer":false}}
"target_K": {"base":12,"perturb":{"mode":"abs","lo":11.0,"hi":13.0,"integer":false}}
"tol": {"base":0.5,"perturb":{"mode":"abs","lo":0.1,"hi":1.5,"integer":false}}
"price": {"base":[21.75,23.5,22.0,19.5,18.5],"perturb":{"mode":"rel","r":0.3}}
"nutrient_N": {"base":[10,8,12,10,15],"perturb":{"mode":"abs","lo":5.0,"hi":18.0,"integer":false}}
"nutrient_P": {"base":[8,11,7,10,10],"perturb":{"mode":"abs","lo":5.0,"hi":14.0,"integer":false}}
"nutrient_K": {"base":[12,15,12,10,6],"perturb":{"mode":"abs","lo":5.0,"hi":16.0,"integer":false}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    target_N = params["target_N"]
    target_P = params["target_P"]
    target_K = params["target_K"]
    tol = params["tol"]
    price = params["price"]
    nutrient_N = params["nutrient_N"]
    nutrient_P = params["nutrient_P"]
    nutrient_K = params["nutrient_K"]

    fertilizers = list(range(1, 6))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(fertilizers, bounds=(0, None))

    # Total percentage composition (percentages are linear, x in 100-lb units)
    model.nitrogen = pyo.Constraint(
        expr=sum(nutrient_N[i - 1] * model.x[i] for i in fertilizers)
        >= target_N * sum(model.x[i] for i in fertilizers)
    )
    model.nitrogen_ub = pyo.Constraint(
        expr=sum(nutrient_N[i - 1] * model.x[i] for i in fertilizers)
        <= (target_N + tol) * sum(model.x[i] for i in fertilizers)
    )
    model.phosphorus = pyo.Constraint(
        expr=sum(nutrient_P[i - 1] * model.x[i] for i in fertilizers)
        >= target_P * sum(model.x[i] for i in fertilizers)
    )
    model.phosphorus_ub = pyo.Constraint(
        expr=sum(nutrient_P[i - 1] * model.x[i] for i in fertilizers)
        <= (target_P + tol) * sum(model.x[i] for i in fertilizers)
    )
    model.potash = pyo.Constraint(
        expr=sum(nutrient_K[i - 1] * model.x[i] for i in fertilizers)
        >= target_K * sum(model.x[i] for i in fertilizers)
    )
    model.potash_ub = pyo.Constraint(
        expr=sum(nutrient_K[i - 1] * model.x[i] for i in fertilizers)
        <= (target_K + tol) * sum(model.x[i] for i in fertilizers)
    )

    # Total mass constraint: produce exactly 100 pounds of mix
    model.total_mass = pyo.Constraint(
        expr=sum(model.x[i] for i in fertilizers) == 1
    )

    model.cost = pyo.Objective(
        expr=sum(price[i - 1] * model.x[i] for i in fertilizers),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"F":[1,2,3,4,5],"J":["N","P","K"]},"params":{"target_N":"minimum nitrogen percentage","target_P":"minimum phosphorus percentage","target_K":"minimum potash percentage","tol":"maximum percentage-point excess","price[F]":"cost per 100 pounds","nutrient_N[F]":"nitrogen percentage","nutrient_P[F]":"phosphorus percentage","nutrient_K[F]":"potash percentage"},"variables":{"x[F]":"continuous nonnegative blend mass fractions"},"constraints":["sum(x[i] for i in F) = 1","target_N <= sum(nutrient_N[i]*x[i] for i in F) <= target_N + tol","target_P <= sum(nutrient_P[i]*x[i] for i in F) <= target_P + tol","target_K <= sum(nutrient_K[i]*x[i] for i in F) <= target_K + tol"],"objective":"minimize sum(price[i]*x[i] for i in F)/100, in dollars per pound"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed mappings (keys 1..5 or '1'..'5') or five-item lists."""

    def indexed_values(values):
        if isinstance(values, Mapping):
            return {
                fertilizer: (
                    values[fertilizer]
                    if fertilizer in values
                    else values[str(fertilizer)]
                )
                for fertilizer in range(1, 6)
            }
        return {
            fertilizer: values[fertilizer - 1]
            for fertilizer in range(1, 6)
        }

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(1, 5)

    model.target_N = pyo.Param(initialize=params["target_N"])
    model.target_P = pyo.Param(initialize=params["target_P"])
    model.target_K = pyo.Param(initialize=params["target_K"])
    model.tol = pyo.Param(initialize=params["tol"])

    model.price = pyo.Param(
        model.F, initialize=indexed_values(params["price"])
    )
    model.nutrient_N = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_N"])
    )
    model.nutrient_P = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_P"])
    )
    model.nutrient_K = pyo.Param(
        model.F, initialize=indexed_values(params["nutrient_K"])
    )

    model.x = pyo.Var(model.F, domain=pyo.NonNegativeReals)

    model.mass_balance = pyo.Constraint(
        expr=sum(model.x[fertilizer] for fertilizer in model.F) == 1
    )

    model.nitrogen_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_N,
            sum(
                model.nutrient_N[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_N + model.tol,
        )
    )
    model.phosphorus_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_P,
            sum(
                model.nutrient_P[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_P + model.tol,
        )
    )
    model.potash_bounds = pyo.Constraint(
        expr=pyo.inequality(
            model.target_K,
            sum(
                model.nutrient_K[fertilizer] * model.x[fertilizer]
                for fertilizer in model.F
            ),
            model.target_K + model.tol,
        )
    )

    # Convert prices per 100 pounds into dollars per pound.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[fertilizer] * model.x[fertilizer]
            for fertilizer in model.F
        ) / 100,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions are allowed to propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrievability alone determines success.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    target_N = params["target_N"]
    target_P = params["target_P"]
    target_K = params["target_K"]
    tol = params["tol"]
    price = params["price"]        # list indexed 0..4 (fertilizers 1..5)
    nutrient_N = params["nutrient_N"]
    nutrient_P = params["nutrient_P"]
    nutrient_K = params["nutrient_K"]

    # Use 0-based indices to match list indexing
    fertilizers = range(5)

    model = gp.Model("fertilizer_mix")
    model.setParam("OutputFlag", 0)

    # x[i] = fraction of fertilizer i in the blend (fractions sum to 1)
    x = {i: model.addVar(lb=0.0, name=f"x_{i}") for i in fertilizers}

    # Blend fractions must sum to 1 (cost per 100 lb of mix)
    model.addConstr(gp.quicksum(x[i] for i in fertilizers) == 1.0, name="sum_to_one")

    # Nitrogen: at least target_N%, no more than target_N + tol %
    model.addConstr(
        gp.quicksum(nutrient_N[i] * x[i] for i in fertilizers) >= target_N,
        name="N_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_N[i] * x[i] for i in fertilizers) <= target_N + tol,
        name="N_upper"
    )

    # Phosphorus: at least target_P%, no more than target_P + tol %
    model.addConstr(
        gp.quicksum(nutrient_P[i] * x[i] for i in fertilizers) >= target_P,
        name="P_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_P[i] * x[i] for i in fertilizers) <= target_P + tol,
        name="P_upper"
    )

    # Potash: at least target_K%, no more than target_K + tol %
    model.addConstr(
        gp.quicksum(nutrient_K[i] * x[i] for i in fertilizers) >= target_K,
        name="K_lower"
    )
    model.addConstr(
        gp.quicksum(nutrient_K[i] * x[i] for i in fertilizers) <= target_K + tol,
        name="K_upper"
    )

    # Minimize cost per 100 lb of blend
    model.setObjective(
        gp.quicksum(price[i] * x[i] for i in fertilizers),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, C-direct; informative instances [0, 2, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 21.606250000000003 (optimal) | 0.2160625 (optimal) | 21.60625 (optimal) |
| 1 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 2 | 18.825150250169145 (optimal) | 0.18825150250169137 (optimal) | 18.82515025016914 (optimal) |
| 3 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 4 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 5 | 23.045405106292954 (optimal) | 0.23045405106292957 (optimal) | 23.045405106292957 (optimal) |

#### independent

Decision: UNINFORMATIVE; clique none; informative instances [0, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 21.606250000000003 (optimal) | 0.2160625 (optimal) | 21.60625 (optimal) |
| 1 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 2 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 3 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 4 | none (infeasible_or_unbounded) | none (infeasible_or_failed) | none (infeasible) |
| 5 | 17.9311215881415 (optimal) | 0.17931121588141502 (optimal) | 17.931121588141504 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 14. om_mamo_205 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_205` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 205) |
| Problem class (OptiMind) | ["Network Optimization"] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_2of3) | 68000.0 |
| Answer (OptiMind) | 70000 |
| Rules that certify it | panel_base_2of3 68000.0 |
| Families agreeing at instance 0 | B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any True (mismatch False, not_stated True) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch True, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
Consider a complex railway network connecting 7 major cities - from the central hub to a key end destination. These cities are interconnected by railway lines, each having a specific capacity for passenger flow.

The capacity of each railway line is as follows, indicating the maximum number of passengers that can travel from one city to another per day:

- From City 0 (Central Hub): Can dispatch passengers to City 1 (18,000 passengers), City 2 (11,000 passengers), City 3 (15,000 passengers), City 4 (2,000 passengers), City 5 (4,000 passengers), and City 6 (20,000 passengers).
- From City 1: Can dispatch passengers to City 0 (4,000 passengers), City 2 (6,000 passengers), City 3 (5,000 passengers), City 4 (19,000 passengers), City 5 (15,000 passengers).
- From City 2: Can dispatch passengers to City 0 (15,000 passengers), City 1 (10,000 passengers), City 3 (7,000 passengers), City 5 (7,000 passengers), and City 6 (5,000 passengers).
- From City 3: Can dispatch passengers to City 0 (14,000 passengers), City 1 (5,000 passengers), City 2 (3,000 passengers), City 4 (10,000 passengers), City 5 (15,000 passengers), and City 6 (19,000 passengers).
- From City 4: Can dispatch passengers to City 0 (2,000 passengers), City 1 (11,000 passengers), City 2 (1,000 passengers), City 3 (10,000 passengers), City 5 (14,000 passengers), and City 6 (6,000 passengers).
- From City 5: Can dispatch passengers to City 0 (10,000 passengers), City 1 (14,000 passengers), City 2 (6,000 passengers), City 3 (5,000 passengers), City 4 (3,000 passengers), City 6 (18,000 passengers).
- From City 6 (End Destination): Can receive passengers from City 0 (8,000 passengers), City 1 (1,000 passengers), City 2 (11,000 passengers), City 3 (8,000 passengers), City 4 (6,000 passengers), and City 5 (20,000 passengers).

In this system, a capacity of "0" signifies there is no direct railway line between those two cities.

Given this situation, we need to determine the maximum number of passengers that can be transported from City 0 (the central hub) to City 6 (the end destination) per day, without exceeding the transportation capacity of any railway line. What is the maximum number of passengers that can be dispatched from the central hub to the end destination per day?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cap_0_1": {"base":18000,"perturb":{"mode":"rel","r":0.5}}
"cap_0_2": {"base":11000,"perturb":{"mode":"rel","r":0.5}}
"cap_0_3": {"base":15000,"perturb":{"mode":"rel","r":0.5}}
"cap_0_4": {"base":2000,"perturb":{"mode":"rel","r":0.5}}
"cap_0_5": {"base":4000,"perturb":{"mode":"rel","r":0.5}}
"cap_0_6": {"base":20000,"perturb":{"mode":"rel","r":0.5}}
"cap_1_0": {"base":4000,"perturb":{"mode":"rel","r":0.5}}
"cap_1_2": {"base":6000,"perturb":{"mode":"rel","r":0.5}}
"cap_1_3": {"base":5000,"perturb":{"mode":"rel","r":0.5}}
"cap_1_4": {"base":19000,"perturb":{"mode":"rel","r":0.5}}
"cap_1_5": {"base":15000,"perturb":{"mode":"rel","r":0.5}}
"cap_2_0": {"base":15000,"perturb":{"mode":"rel","r":0.5}}
"cap_2_1": {"base":10000,"perturb":{"mode":"rel","r":0.5}}
"cap_2_3": {"base":7000,"perturb":{"mode":"rel","r":0.5}}
"cap_2_5": {"base":7000,"perturb":{"mode":"rel","r":0.5}}
"cap_2_6": {"base":5000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_0": {"base":14000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_1": {"base":5000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_2": {"base":3000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_4": {"base":10000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_5": {"base":15000,"perturb":{"mode":"rel","r":0.5}}
"cap_3_6": {"base":19000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_0": {"base":2000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_1": {"base":11000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_2": {"base":1000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_3": {"base":10000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_5": {"base":14000,"perturb":{"mode":"rel","r":0.5}}
"cap_4_6": {"base":6000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_0": {"base":10000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_1": {"base":14000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_2": {"base":6000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_3": {"base":5000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_4": {"base":3000,"perturb":{"mode":"rel","r":0.5}}
"cap_5_6": {"base":18000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_0": {"base":8000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_1": {"base":1000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_2": {"base":11000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_3": {"base":8000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_4": {"base":6000,"perturb":{"mode":"rel","r":0.5}}
"cap_6_5": {"base":20000,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Build arc list with capacities from params
    arcs = []
    capacities = {}
    for i in range(7):
        for j in range(7):
            if i == j:
                continue
            key = "cap_%d_%d" % (i, j)
            if key in params:
                arcs.append((i, j))
                capacities[(i, j)] = params[key]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    source = 0
    sink = 6
    nodes = range(7)

    def cap_rule(model, i, j):
        return model.flow[i, j] <= capacities[(i, j)]
    model.cap_limit = pyo.Constraint(model.ARCS, rule=cap_rule)

    def conservation_rule(model, k):
        inflow = sum(model.flow[i, k] for (i, j) in arcs if j == k)
        outflow = sum(model.flow[k, j] for (i, j) in arcs if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.conservation = pyo.Constraint(nodes, rule=conservation_rule)

    def obj_rule(model):
        return sum(model.flow[source, j] for (i, j) in arcs if i == source)
    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_flow))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":[0,1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j} excluding (1,6) and (2,4)"},"params":{"capacity[i,j]":"params['cap_i_j'] for every (i,j) in A; keys denote directed arcs i -> j, including keys starting with cap_6_"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[0,j] - sum_i flow[i,0] = throughput","sum_j flow[v,j] - sum_i flow[i,v] = 0 for v in {1,2,3,4,5}","sum_i flow[i,6] - sum_j flow[6,j] = throughput"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(7))
    arcs = tuple(
        (origin, destination)
        for origin in vertices
        for destination in vertices
        if origin != destination
        and (origin, destination) not in {(1, 6), (2, 4)}
    )
    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        city: tuple(destination for origin, destination in arcs if origin == city)
        for city in vertices
    }
    incoming = {
        city: tuple(origin for origin, destination in arcs if destination == city)
        for city in vertices
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=vertices, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.arc_capacity = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, city):
        departures = sum(
            network.flow[city, destination]
            for destination in outgoing[city]
        )
        arrivals = sum(
            network.flow[origin, city]
            for origin in incoming[city]
        )
        if city == 0:
            return departures - arrivals == network.throughput
        if city == 6:
            return arrivals - departures == network.throughput
        return departures - arrivals == 0

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)
    model.max_throughput = pyo.Objective(
        expr=model.throughput, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    # Edges that exist in the network
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 5), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]

    cap = {}
    for (i, j) in edges:
        key = f"cap_{i}_{j}"
        cap[(i, j)] = params[key]

    source = 0
    sink = 6
    nodes = list(range(7))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap[(i, j)], name=f"flow_{i}_{j}")

    # Objective: maximize flow into sink
    model.setObjective(
        gp.quicksum(flow[(i, sink)] for (i, j) in edges if j == sink),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 70000.0 (optimal) | 68000.0 (optimal) | 68000.0 (optimal) |
| 1 | 67836.53653663995 (optimal) | 67836.53653663996 (optimal) | 81619.72766888008 (optimal) |
| 2 | 57158.59696897344 (optimal) | 57158.59696897344 (optimal) | 59718.27151058014 (optimal) |
| 3 | 64543.23693295432 (optimal) | 59812.551537079045 (optimal) | 59812.55153707904 (optimal) |
| 4 | 73883.87698112258 (optimal) | 67055.29328626095 (optimal) | 67055.29328626096 (optimal) |
| 5 | 53320.6634601013 (optimal) | 53320.6634601013 (optimal) | 67273.84175864513 (optimal) |

#### independent

Decision: ABSTAIN; clique none; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 70000.0 (optimal) | 68000.0 (optimal) | 68000.0 (optimal) |
| 1 | 67836.53653663995 (optimal) | 67836.53653663996 (optimal) | 81619.72766888008 (optimal) |
| 2 | 57158.59696897344 (optimal) | 57158.59696897344 (optimal) | 59718.27151058014 (optimal) |
| 3 | 64543.23693295432 (optimal) | 59812.551537079045 (optimal) | 59812.55153707904 (optimal) |
| 4 | 73883.87698112258 (optimal) | 67055.29328626095 (optimal) | 67055.29328626096 (optimal) |
| 5 | 53320.6634601013 (optimal) | 53320.6634601013 (optimal) | 67273.84175864513 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch": [], "not_stated": [{"parameter": "cap_1_5", "evidence": "From City 1: Can dispatch passengers to ... City 5 (15,000 passengers)"}]}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{
  "mismatch": [
    {
      "parameter": "cap_6_0",
      "extracted": 8000,
      "stated": "8000 from City 0 to City 6",
      "evidence": "From City 6 (End Destination): Can receive passengers from City 0 (8,000 passengers)"
    },
    {
      "parameter": "cap_6_1",
      "extracted": 1000,
      "stated": "1000 from City 1 to City 6",
      "evidence": "Can receive passengers from ... City 1 (1,000 passengers)"
    },
    {
      "parameter": "cap_6_2",
      "extracted": 11000,
      "stated": "11000 from City 2 to City 6",
      "evidence": "Can receive passengers from ... City 2 (11,000 passengers)"
    },
    {
      "parameter": "cap_6_3",
      "extracted": 8000,
      "stated": "8000 from City 3 to City 6",
      "evidence": "Can receive passengers from ... City 3 (8,000 passengers)"
    },
    {
      "parameter": "cap_6_4",
      "extracted": 6000,
      "stated": "6000 from City 4 to City 6",
      "evidence": "Can receive passengers from ... City 4 (6,000 passengers)"
    },
    {
      "parameter": "cap_6_5",
      "extracted": 20000,
      "stated": "20000 from City 5 to City 6",
      "evidence": "Can receive passengers from ... City 5 (20,000 passengers)"
    }
  ],
  "not_stated": []
}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "cap_6_0",
      "extracted": 8000,
      "stated": 20000,
      "evidence": "From City 0 (Central Hub): Can dispatch passengers to... City 6 (20,000 passengers)"
    },
    {
      "parameter": "cap_6_1",
      "extracted": 1000,
      "stated": 0,
      "evidence": "From City 1: Can dispatch passengers to City 0 (4,000 passengers), City 2 (6,000 passengers), City 3 (5,000 passengers), City 4 (19,000 passengers), City 5 (15,000 passengers). [City 6 not listed]"
    },
    {
      "parameter": "cap_6_2",
      "extracted": 11000,
      "stated": 5000,
      "evidence": "From City 2: Can dispatch passengers to... City 6 (5,000 passengers)"
    },
    {
      "parameter": "cap_6_3",
      "extracted": 8000,
      "stated": 19000,
      "evidence": "From City 3: Can dispatch passengers to... City 6 (19,000 passengers)"
    },
    {
      "parameter": "cap_6_5",
      "extracted": 20000,
      "stated": 18000,
      "evidence": "From City 5: Can dispatch passengers to... City 6 (18,000 passengers)"
    }
  ],
  "not_stated": []
}
```
````

