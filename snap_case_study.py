
## import necessary packages ##
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import webbrowser

## set up file path and empty db ##
xls_path = "C:/Users/nrowe/Downloads/sample_datasets.xlsx"
db_path = "snap_takehome.db"

## load tables ##
applications = pd.read_excel(xls_path, sheet_name="applications")
customers = pd.read_excel(xls_path, sheet_name="customers")
stores = pd.read_excel(xls_path, sheet_name="stores")
marketing = pd.read_excel(xls_path, sheet_name="marketing")

## create tables in sqlite ##
conn = sqlite3.connect(db_path)

applications.to_sql("applications", conn, if_exists="replace", index=False)
customers.to_sql("customers", conn, if_exists="replace", index=False)
stores.to_sql("stores", conn, if_exists="replace", index=False)
marketing.to_sql("marketing", conn, if_exists="replace", index=False)

conn.commit()

## sanity check ##
pd.read_sql("select name from sqlite_master where type='table' order by name;", conn)

### Task1 [# of apps, approved, used apps, vizualize trend over sub date] ###

sql = """select
    strftime('%Y-%m-%d', submit_date) as dt,
    count(application_id) as applications,
    sum(case when approved = 1 then 1 else 0 end) as approved,
    sum(case when dollars_used > 0 then 1 else 0 end) as used_apps
from applications
group by dt
order by dt"""

task1 = pd.read_sql(sql, conn)

task1.head()

x = np.arange(len(task1))

plt.figure()

plt.plot(x, task1["applications"], label="Applications")
plt.plot(x, task1["approved"], label="Approved")
plt.plot(x, task1["used_apps"], label="Used")

plt.title("Application Funnel Trend")
plt.xlabel("Submission Date")
plt.ylabel("Number of Applications")

plt.xticks(x, task1["dt"], rotation=45)

plt.legend()

plt.tight_layout()
plt.show()

## Thats too granular and looks messy, so let's get it by month-year instead

sql = """select
    strftime('%Y-%m', submit_date) as mnth,
    count(application_id) as applications,
    sum(case when approved = 1 then 1 else 0 end) as approved,
    sum(case when dollars_used > 0 then 1 else 0 end) as used_apps
from applications
group by mnth
order by mnth;"""

task1_monthly = pd.read_sql(sql, conn)

task1_monthly.head()

x = np.arange(len(task1_monthly))

plt.figure()

plt.plot(x, task1_monthly["applications"], label="Applications")
plt.plot(x, task1_monthly["approved"], label="Approved")
plt.plot(x, task1_monthly["used_apps"], label="Used")

plt.title("Application Funnel Trend")
plt.xlabel("Submission Date")
plt.ylabel("Number of Applications")

plt.xticks(x, task1_monthly["mnth"], rotation=45)

plt.legend()

plt.tight_layout()
plt.show()



### Task2: Avg approved vs used amount over submission date ###

sql = """select 
avg(approved_amount) as avg_approved_amount, avg(dollars_used) as avg_dollars_used, strftime('%Y-%m', submit_date) as mnth 
from applications 
where approved is TRUE 
group by strftime('%Y-%m', submit_date);"""

monthly_spend = pd.read_sql(sql, conn)

a = np.arange(len(monthly_spend))
b = monthly_spend["avg_approved_amount"]
c = monthly_spend["avg_dollars_used"]

plt.figure()
plt.plot(a, b, color="red", label="Avg Approved Amount")
plt.plot(a, c, color="blue", label="Avg Used Amount")

b_trend = np.polyfit(a, b, 1)
c_trend = np.polyfit(a, c, 1)
b_trendline = np.poly1d(b_trend)
c_trendline = np.poly1d(c_trend)

plt.plot(x, b_trendline(a), linestyle="--", color="green", label="Approved Trend")
plt.plot(x, c_trendline(a), linestyle="--", color="green", label="Used Trend")

plt.title("Average Approved vs Average Used Amount Trends")
plt.ylabel("Amount ($)")
plt.xlabel("Month")
plt.ylim(0, 4000)

plt.xticks(x, monthly_spend["mnth"].astype(str), rotation=45)

plt.legend()

plt.tight_layout()
plt.show()



## Task3: 

sql = ("""select
    store,
    count(distinct application_id) as applications,
    sum(case when approved = 1 then 1 else 0 end) as approved_apps,
    sum(case when dollars_used > 0 then 1 else 0 end) as used_apps,
    round(sum(approved_amount), 0) as total_approved_amount,
    round(sum(dollars_used)) as total_used_amount,
    round(cast(sum(case when approved = 1 then 1 else 0 end) as float) / count(distinct application_id), 4) as approval_rate,
    round(cast(sum(case when dollars_used > 0 then 1 else 0 end) as float) / cast(nullif(sum(case when approved = 1 then 1 else 0 end),0) as float), 4) as usage_rate,
    round(cast(sum(case when dollars_used > 0 then 1 else 0 end) as float) / count(distinct application_id), 4) as avg_efficiency 
from applications
group by store
order by avg_efficiency desc;""")

task3 = pd.read_sql(sql, conn)

print(task3)

cleaned = task3.style.format({
    "total_approved_amount": "${:,.0f}",
    "total_used_amount": "${:,.0f}",
    "approval_rate": "{:.2f}%",
    "usage_rate": "{:.2f}%",
    "avg_efficiency": "{:.2f}%"
})

cleaned.to_html("store_metrics_table.html")

webbrowser.open("store_metrics_table.html")



### Task4: Graph to compare used dollar amount vs spend amount by Marketing ###

sql = ("""
select
    m.name as marketing_name,
    sum(a.dollars_used) as total_used_amount,
    m.spend
from applications a
left join customers c
    on a.customer_id = c.customer_id
left join marketing m
    on c.campaign = m.id
group by m.name, m.spend;""")

task4 = pd.read_sql(sql, conn)

x = np.arange(len(task4))
width = 0.35

plt.figure()

plt.bar(x - width/2, task4["total_used_amount"],
        width, label="Used Dollars")

plt.bar(x + width/2, task4["spend"],
        width, label="Marketing Spend")

plt.xticks(x, task4["marketing_name"], rotation=45)

plt.ylabel("Amount ($)")
plt.title("Marketing Spend vs Used Dollars by Campaign")

plt.legend()

plt.tight_layout()
plt.show()

## What is the ROI though? Which is best? ##

task4["roi"] = task4["total_used_amount"] / task4["spend"]

task4["roi"] = task4["total_used_amount"] / task4["spend"]
task4_sorted = task4.sort_values("roi", ascending=False)

plt.figure()

plt.bar(task4_sorted["marketing_name"], task4_sorted["roi"])

plt.title("Marketing Campaign ROI")
plt.ylabel("ROI (Used Dollars per $1 Spent)")
plt.xlabel("Campaign")

plt.xticks(rotation=45)

plt.tight_layout()
plt.show()



### Task5: find something interesting

# Building on what was found in Task4, here's a breakdown of the ROI, because credit utilization seems to be the only thing that SNAP doesn't control. So getting that insight seems the most valuable

sql = """select 
    marketing_name,
    total_used_amount,
    spend,
    (cast(total_used_amount as float) / cast(spend as float)) as ROI,
    (cast(total_used_amount as float) / cast(applications as float)) as used_per_application,
    (cast(approved_apps - used_apps as float) / nullif(cast(approved_apps as float), 0)) as unused_rate
from 
    (select
     m.name as marketing_name,
     count(a.application_id) as applications,
     sum(a.dollars_used) as total_used_amount,
     m.spend,
     sum(case when a.approved = 1 then 1 else 0 end) as approved_apps,
     sum(case when a.approved = 1 and coalesce(a.dollars_used, 0) > 0 then 1 else 0 end) as used_apps
from applications a
left join customers c on a.customer_id = c.customer_id
left join marketing m on c.campaign = m.id
group by m.name, m.spend)
order by ROI desc;"""

marketing_efficiency = pd.read_sql(sql, conn)

marketing_efficiency = marketing_efficiency.rename(columns={
    "marketing_name":"Campaign",
    "applications":"Applications",
    "total_used_amount":"Total Used",
    "spend":"Marketing Spend",
    "ROI":"ROI",
    "used_per_application":"Used per Application",
    "unused_rate":"Unused Approval Rate"
})

cleaned = marketing_efficiency.style.format({
    "Total Used":"${:,.0f}",
    "Marketing Spend":"${:,.0f}",
    "ROI":"{:.2f}x",
    "Unused Approval Rate": "{:.2f}%"
})

cleaned.to_html("marketing_roi_table.html")

webbrowser.open("marketing_roi_table.html")

# I was hoping there would be a correlation between time it takes to approve the loan and utilization rate, but there's not. Even when you break it out by days, minutes, or even buckets.

df = pd.read_sql("select * from applications", conn)
df["submit_date"] = pd.to_datetime(df["submit_date"])
df["approved_date"] = pd.to_datetime(df["approved_date"])
df = df[df["approved"] == 1]
df["utilization"] = df["dollars_used"] / df["approved_amount"]

df["approval_days"] = (df["approved_date"] - df["submit_date"]).dt.days
df[["approval_days","utilization"]].corr()

df["approval_minutes"] = (df["approved_date"] - df["submit_date"]).dt.total_seconds() / 60
df[["approval_minutes","utilization"]].corr()

df["approval_bucket"] = pd.cut(df["approval_minutes"], bins=[0,1,1440,2880,4320,10000], labels=["instant","1 day","2 days","3 days",">3 days"], include_lowest=True )
bucket_stats = df.groupby("approval_bucket").agg(avg_utilization=("utilization","mean"), applications=("application_id","count"))
print(bucket_stats)
bucket_map = {"instant":0, "1 day":1, "2 days":2, "3 days":3, ">3 days":4}
df["bucket_numeric"] = df["approval_bucket"].map(bucket_map)
df[["bucket_numeric","utilization"]].corr()

