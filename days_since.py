# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import altair as alt


def get_df(path):
    df = pd.read_csv(path)
    cols = [col for col in df if col not in ["Lat", "Long", "Province/State"]]
    df = df[cols].rename(columns={"Country/Region": "country"})
    df = df.melt(id_vars="country", var_name="date", value_name="total_cases")
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").groupby("country").resample("D").sum().reset_index()


@st.cache
def get_confirmed_df():
    df = get_df("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv")
    df["days_since"] = df.assign(t=df.total_cases > 99).groupby("country")["t"].cumsum()
    return df[df["days_since"] > 0]


@st.cache
def get_deaths_df():
    df = get_df("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv")
    df = df.rename(columns={"total_cases": "total_deaths"})
    df["days_since"] = (df.assign(t=df.total_deaths >= 1).groupby("country")["t"].cumsum())
    return df[df["days_since"] > 0]


if __name__ == "__main__":
    df_confirmed = get_confirmed_df()
    df_deaths = get_deaths_df()

    st.title("COVID-19 🦠")

    top_10 = (
        df_confirmed[df_confirmed["country"] != "China"]
        .groupby("country")["total_cases"]
        .max()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )

    select_all = df_confirmed["country"].unique().tolist()

    radio = st.radio("", ["Top 10, excluding China", "US vs Italy", "Select All"])

    if radio == "Top 10, excluding China":
        country = st.multiselect("", select_all, default=top_10)
    elif radio == "Select All":
        country = st.multiselect("", select_all, default=select_all)
    elif radio == "US vs Italy":
        country = st.multiselect("", select_all, default=["US", "Italy"])

    df_confirmed_filtered = df_confirmed[df_confirmed["country"].isin(country)]

    st.write("")
    st.write("Confirmed cases by days since 100th case 😷")

    c = (
        alt.Chart(df_confirmed_filtered, width=750, height=500)
        .mark_line(point=True)
        .encode(
            x="days_since",
            y=alt.Y("total_cases", scale=alt.Scale(type="log", base=10)),
            color="country",
            tooltip=[alt.Tooltip("country"), alt.Tooltip("total_cases", format=",")],
        )
        .interactive()
    )

    st.altair_chart(c)

    df_deaths_filtered = df_deaths[df_deaths["country"].isin(country)]

    st.write("Deaths by days since 1st case")

    c2 = (
        alt.Chart(df_deaths_filtered, width=750, height=500)
        .mark_line(point=True)
        .encode(
            x="days_since",
            y=alt.Y("total_deaths", scale=alt.Scale(type="log", base=10)),
            color="country",
            tooltip=[alt.Tooltip("country"), alt.Tooltip("total_deaths", format=",")],
        )
        .interactive()
    )

    st.altair_chart(c2)
