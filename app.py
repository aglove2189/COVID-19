# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import altair as alt


def get_df(type):
    path = f"https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-{type}.csv"
    df = pd.read_csv(path)
    cols = [col for col in df if col not in ["Lat", "Long", "Province/State"]]
    df = df[cols].rename(columns={"Country/Region": "country"})
    df["country"] = df["country"].replace({"US": "United States", "Korea, South": "South Korea"})
    df = df.melt(id_vars="country", var_name="date", value_name=f"total_{type}".lower())
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").groupby("country").resample("D").sum().reset_index()


def days_since(df, col, num=100):
    df["days_since"] = df.assign(t=df[col] >= num).groupby("country")["t"].cumsum()
    return df[df["days_since"] > 0]


def chart(df, y):
    return (
        alt.Chart(df, width=750, height=500)
        .mark_line(point=True)
        .encode(
            x="days_since",
            y=alt.Y(y, scale=alt.Scale(type="log", base=10)),
            color="country",
            tooltip=[alt.Tooltip("country"), alt.Tooltip(y, format=",")],
        )
        .interactive()
    )


if __name__ == "__main__":
    st.title("COVID-19 🦠")

    confirmed_df = get_df("Confirmed")
    deaths_df = get_df("Deaths")

    num_confirmed = st.text_input("Number of Confirmed:", 100)
    confirmed_since_df = days_since(confirmed_df, "total_confirmed", num=int(num_confirmed))

    top_10 = (
        confirmed_since_df[confirmed_since_df["country"] != "China"]
        .groupby("country")["total_confirmed"]
        .max()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )

    select_all = confirmed_since_df["country"].unique().tolist()
    selection = ["Top 10, excluding China", "US vs Italy vs South Korea", "Select All"]
    radio = st.sidebar.radio("", selection)

    if radio == "Top 10, excluding China":
        country = st.sidebar.multiselect("", select_all, default=top_10)
    elif radio == "Select All":
        country = st.sidebar.multiselect("", select_all, default=select_all)
    elif radio == "US vs Italy vs South Korea":
        default = ["United States", "Italy", "South Korea"]
        country = st.sidebar.multiselect("", select_all, default=default)

    confirmed_since_df = confirmed_since_df[confirmed_since_df["country"].isin(country)]

    st.write(f"Confirmed cases by days since {num_confirmed} confirmed 😷")
    st.altair_chart(chart(confirmed_since_df, "total_confirmed"))

    num_deaths = st.text_input("Number of Death(s):", 1)
    deaths_since_df = days_since(deaths_df, "total_deaths", num=int(num_deaths))
    deaths_since_df = deaths_since_df[deaths_since_df["country"].isin(country)]

    st.write(f"Deaths by days since {num_deaths} death(s)")
    st.altair_chart(chart(deaths_since_df, "total_deaths"))

    st.write("Totals")
    df = df = pd.concat([
        confirmed_df.groupby("country")["total_confirmed"].max(),
        deaths_df.groupby("country")["total_deaths"].max()
    ], axis=1).sort_values("total_deaths", ascending=False).style.format("{:,}")

    st.dataframe(df)
