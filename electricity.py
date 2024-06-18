import pandas as pd
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def calc_var_plan_tier_amounts(weekday, input_date, input_df, input_col):
    kWh_day_out, kWh_life_out, kWh_night_out = 0, 0, 0
    if weekday == True:
        for k,v in weekday_times.items():
            kWh_sum = get_tier_amounts(input_date, input_df, input_col, v)
            if k == "tier_day":
                kWh_day_out += kWh_sum
            if k == "tier_life":
                kWh_life_out += kWh_sum
            if k == "tier_night":
                kWh_night_out += kWh_sum
    elif weekday == False:
        for k,v in weekend_times.items():
            kWh_sum = get_tier_amounts(input_date, input_df, input_col, v)
            if k == "tier_day":
                kWh_day_out += kWh_sum
            if k == "tier_life":
                kWh_life_out += kWh_sum
            if k == "tier_night":
                kWh_night_out += kWh_sum
    return kWh_day_out, kWh_life_out, kWh_night_out

def calc_standard_plan_tier_amounts(input_df, col_names):
    kWh_raw = input_df.drop(col_names[0], axis=1).to_numpy().sum()
    if (total_kWh := round_float(kWh_raw, 0)) > 300:
        tier_3 = total_kWh - 300
        tier_2 = 300 - 120
        tier_1 = 120
    elif total_kWh < 300 and total_kWh > 120:
        tier_3 = 0
        tier_2 = total_kWh - 120
        tier_1 = 120
    else:
        tier_3 = 0
        tier_2 = 0
        tier_1 = total_kWh
    return tier_1, tier_2, tier_3

def convert_to_datetime_object(input_date, input_format):
    date = datetime.strptime(input_date, input_format)
    return date

def get_tier_amounts(input_date, input_df, input_col, input_val):
    date_str = input_date.strftime("%Y/%m/%d")
    date_val_all = input_df.loc[input_df[input_col]==date_str]
    date_val_sub = date_val_all[date_val_all.columns.intersection(input_val)]
    kWh_sum_out = date_val_sub.to_numpy().sum()
    return kWh_sum_out

def print_cost(input_cost, input_plan):
    if input_plan == "Standard Plan":
        cost_rounded = round_float(input_cost,0)
        print(f"* Total cost for {input_plan}: {cost_rounded:,} JPY")
    else:
        cost_rounded = round_float(input_cost,0)
        cost_diff = round_float(input_cost-total_cost_standard,0)
        if cost_diff < 0:
            more_less = "less"
        else:
            more_less = "more"
        print(f"* Total cost for {input_plan}: {cost_rounded:,} JPY "
              f"({cost_diff} JPY {more_less} vs Standard Plan)")        

def print_divider():
    print(f'\n{"+"*40}')

def round_float(input_float, input_to):
    rounded = int(round(Decimal(input_float), input_to))
    return rounded


#------------------------------------------------------------------------------
# STEP 0: Define global constants and variables
#------------------------------------------------------------------------------

root_dir = Path(Path.cwd().parents[0], 'info_files', 'electricity.txt')

standard_plan = {"base_charge": 796.06,
                 "tier_1": 19.67,
                 "tier_2": 24.78,
                 "tier_3": 27.71
                 }

night_plan = {"base_charge": 565.20,
              "tier_day": 26.25,
              "tier_life": 32.65,
              "tier_night": 18.88
              }

day_plan = {"base_charge": 565.20,
            "tier_day": 20.05,
            "tier_life": 32.65,
            "tier_night": 22.98
            }

weekday_times = {"tier_day": [9,10,11,12,13,14,15],
                 "tier_life": [6,7,8,16,17,18,19,20,21,22],
                 "tier_night": [0,1,2,3,4,5,23]
                 }

weekend_times = {"tier_day": [8,9,10,11,12,13,14,15,16,17,18,19,20,21],
                 "tier_life": [],
                 "tier_night": [0,1,2,3,4,5,6,7,22,23]
                 }

day_name = {0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday"
            }


#------------------------------------------------------------------------------
# STEP 1: Import data
#------------------------------------------------------------------------------

# Get raw data file directory
with open(root_dir, encoding="utf-8") as input_file:
    root_dir = Path(input_file.read())

#Generate list with every file in root directory
file_list = [i for i in root_dir.glob('**/*')]
print(f'Total Number of Items Found: {len(file_list)}')

# Process each file found above
for raw_data_file in file_list:

    # Import data
    input_file_str = str(raw_data_file) #input("Input source data file: ")

    # Clean up input string
    if (input_file_str.startswith('"') == True 
        and input_file_str.endswith('"') == True):
        input_file = Path(input_file_str[1:-1])
    else:
        input_file = Path(input_file_str)

    # Import data into dataframe
    df_raw = pd.read_csv(input_file)

    # Reformat columns for easier processing
    col_names = df_raw.columns.tolist()
    col_num = [int(y.strip('時台')) for y in col_names[1:]]
    col_new = [col_names[0]] + col_num
    df_raw.columns = col_new

    # Get date of data file
    date_raw = input_file.name
    date_file = re.search("(?<=_).*(?=.csv)", date_raw)


    #--------------------------------------------------------------------------
    # STEP 2: Determine cost of the standard plan
    #--------------------------------------------------------------------------

    # Determine cost using the standard plan
    kWh_tier_amounts = calc_standard_plan_tier_amounts(df_raw, col_new)
    print_divider()
    print(f"\nElectricity consumption by tier for {date_file.group()} "
        f"(Standard Plan):\n"
        f"0-120 kWh: {kWh_tier_amounts[0]} kWh\n"
        f"121-300 kWh: {kWh_tier_amounts[1]} kWh\n"
        f"301+ kWh: {kWh_tier_amounts[2]} kWh")

    total_cost_standard = (standard_plan["base_charge"] 
                        + kWh_tier_amounts[0]*standard_plan["tier_1"] 
                        + kWh_tier_amounts[1]*standard_plan["tier_2"] 
                        + kWh_tier_amounts[2]*standard_plan["tier_3"]
                        )
    print(f"* Total kWh consumed: {sum(kWh_tier_amounts)} kWh")
    print_cost(total_cost_standard, "Standard Plan")


    #--------------------------------------------------------------------------
    # STEP 3: Determine consumption for the night and day plans
    #--------------------------------------------------------------------------

    # Initialize kWh variables
    kWh_day, kWh_life, kWh_night = 0, 0, 0

    # Calculate tier consumption on a daily basis
    for x in range(len(df_raw)):
        # Determine if the day is a weekday or not
        date = convert_to_datetime_object(df_raw[col_new[0]][x],"%Y/%m/%d")
        if date.weekday() in [5,6]:
            weekday = False
        else:
            weekday = True
        
        # Sum up consumption amounts by tier
        tier_amts = calc_var_plan_tier_amounts(
            weekday, date, df_raw, col_new[0])
        kWh_day += tier_amts[0]
        kWh_life += tier_amts[1]
        kWh_night += tier_amts[2]

    # Display total electricity consumption by tier
    print(f"\nElectricity consumption by tier for {date_file.group()} "
        f"(Night/Day Plans):\n"
        f"Day: {kWh_day:.0f} kWh\n"
        f"Life: {kWh_life:.0f} kWh\n"
        f"Night: {kWh_night:.0f} kWh")
    print(f"* Total kWh consumed: {(kWh_day + kWh_life + kWh_night):.0f} kWh")

    #--------------------------------------------------------------------------
    # STEP 4: Determine cost of the night and day plans
    #--------------------------------------------------------------------------

    # Calculate the cost for each tier (night)
    night_tier_day_cost = kWh_day*night_plan["tier_day"]
    night_tier_life_cost = kWh_life*night_plan["tier_life"]
    night_tier_night_cost = kWh_night*night_plan["tier_night"]

    # Display total cost of the night plan
    total_cost_night = (night_plan["base_charge"] + night_tier_day_cost 
                        + night_tier_life_cost + night_tier_night_cost)
    print_cost(total_cost_night, "Night Plan")

    # Calculate the cost for each tier (day)
    day_tier_day_cost = kWh_day*day_plan["tier_day"]
    day_tier_life_cost = kWh_life*day_plan["tier_life"]
    day_tier_night_cost = kWh_night*day_plan["tier_night"]

    # Display total cost of the day plan
    total_cost_day = (day_plan["base_charge"] + day_tier_day_cost 
                    + day_tier_life_cost + day_tier_night_cost)
    print_cost(total_cost_day, "Day Plan")
    print_divider()