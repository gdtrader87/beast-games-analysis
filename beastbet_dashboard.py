"""
BeastBet Live - Interactive Streamlit Dashboard

Production-grade dashboard for real-time prediction market viewing,
betting placement, portfolio tracking, and revenue metrics.

Features:
- Live competition view with real-time odds updates
- Betting interface with order management
- User portfolio and leaderboard
- Market intelligence and revenue dashboards
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from decimal import Decimal
import time
import random
from beastbet_core import (
    PredictionMarket, create_mock_competition, BetOutcome, Decimal
)

# Page config
st.set_page_config(
    page_title="BeastBet Live",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .winner-box {
        background-color: #90EE90;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .loser-box {
        background-color: #FFB6C1;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_market():
    """Initialize or retrieve cached market instance."""
    market = create_mock_competition("Beast Games Live")
    
    # Add some sample bets to make it realistic
    sample_users = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    for i, user_id in enumerate(sample_users):
        for j, contestant_id in enumerate(list(market.contestants.keys())[:3]):
            amount = Decimal(str(random.randint(10, 500)))
            market.place_bet(user_id, contestant_id, amount)
    
    return market


def format_currency(value):
    """Format value as currency."""
    return f"${value:,.2f}"


def render_live_odds_section(market: PredictionMarket):
    """Render live odds and competition view."""
    st.header("🔴 LIVE ODDS")
    
    # Get market data
    summary = market.get_market_summary()
    
    # Create two-column layout: odds grid and market stats
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Odds & Volume")
        
        # Create odds cards
        cols = st.columns(len(market.contestants))
        for idx, (c_id, contestant) in enumerate(market.contestants.items()):
            with cols[idx]:
                implied_prob = market.calculate_implied_probability(c_id)
                
                st.markdown(f"""
                    <div class="metric-box">
                        <h3 style="margin: 0;">{contestant.name}</h3>
                        <p style="font-size: 24px; color: #1f77b4; margin: 10px 0;"><b>{float(contestant.current_odds):.2f}</b></p>
                        <p style="margin: 5px 0; color: #666;">Vol: ${float(contestant.total_volume):,.0f}</p>
                        <p style="margin: 5px 0; color: #666;">Bets: {contestant.bets_placed}</p>
                        <p style="margin: 5px 0; color: #666;">Win%: {float(implied_prob)*100:.1f}%</p>
                    </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Market Stats")
        st.metric("Total Volume", format_currency(summary['total_volume']))
        st.metric("GMV", format_currency(summary['gmv']))
        st.metric("Open Bets", summary['total_open_bets'])
        st.metric("Rake Collected", format_currency(summary['total_rake_collected']))


def render_betting_interface(market: PredictionMarket):
    """Render the betting interface."""
    st.header("🎯 PLACE BET")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        user_id = st.text_input("User ID", value="user_001", key="bet_user")
    
    with col2:
        contestant_options = {c.name: c.id for c in market.contestants.values()}
        selected_contestant = st.selectbox(
            "Select Contestant",
            list(contestant_options.keys()),
            key="bet_contestant"
        )
        contestant_id = contestant_options[selected_contestant]
    
    with col3:
        bet_amount = st.number_input(
            "Bet Amount ($)",
            min_value=1,
            max_value=10000,
            value=50,
            step=10,
            key="bet_amount"
        )
    
    # Show odds for selected contestant
    contestant = market.get_contestant(contestant_id)
    if contestant:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Odds", f"{float(contestant.current_odds):.2f}")
        with col2:
            potential_win = Decimal(str(bet_amount)) * contestant.current_odds
            st.metric("Potential Win", format_currency(potential_win))
        with col3:
            profit = potential_win - Decimal(str(bet_amount))
            st.metric("Profit", format_currency(profit))
    
    # Betting buttons in a row
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🎲 PLACE BET", key="btn_place_bet", use_container_width=True):
            try:
                bet = market.place_bet(user_id, contestant_id, Decimal(str(bet_amount)))
                st.success(f"✅ Bet placed! ID: {bet.id}")
                st.balloons()
            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if st.button("Cancel", key="btn_cancel", use_container_width=True):
            st.info("Cancelled")


def render_portfolio_section(market: PredictionMarket):
    """Render user portfolio and performance."""
    st.header("📊 YOUR PORTFOLIO")
    
    user_id = st.selectbox(
        "Select User",
        ["user_001", "user_002", "user_003", "user_004", "user_005"],
        key="portfolio_user"
    )
    
    portfolio = market.get_user_portfolio(user_id)
    
    if not portfolio:
        st.info("No portfolio data for this user")
        return
    
    # Portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Wagered",
            format_currency(portfolio.total_wagered),
            delta=f"{float(portfolio.total_wagered):,.0f} units"
        )
    
    with col2:
        st.metric(
            "Total Won",
            format_currency(portfolio.total_won),
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Total Lost",
            format_currency(portfolio.total_lost),
            delta_color="off"
        )
    
    with col4:
        st.metric(
            "ROI",
            f"{float(portfolio.roi_percentage):.2f}%",
            delta_color="inverse"
        )
    
    st.divider()
    
    # User's bets
    st.subheader("Open Bets")
    open_bets = market.get_user_bets(user_id, BetOutcome.PENDING)
    
    if open_bets:
        bets_data = []
        for bet in open_bets:
            contestant = market.get_contestant(bet.contestant_id)
            payout = bet.amount * bet.odds_at_placement
            profit = payout - bet.amount
            
            bets_data.append({
                "Bet ID": bet.id,
                "Contestant": contestant.name if contestant else "Unknown",
                "Amount": format_currency(bet.amount),
                "Odds": f"{float(bet.odds_at_placement):.2f}",
                "Potential Payout": format_currency(payout),
                "Profit": format_currency(profit),
                "Placed": bet.timestamp.strftime("%H:%M:%S")
            })
        
        df_bets = pd.DataFrame(bets_data)
        st.dataframe(df_bets, use_container_width=True, hide_index=True)
    else:
        st.info("No open bets")
    
    st.divider()
    
    # Settled bets
    st.subheader("Recent Settlements")
    settled_bets = market.get_user_bets(user_id)
    settled_bets = [b for b in settled_bets if b.status != BetOutcome.PENDING][:5]
    
    if settled_bets:
        settled_data = []
        for bet in settled_bets:
            contestant = market.get_contestant(bet.contestant_id)
            status_emoji = "✅" if bet.status == BetOutcome.WON else "❌"
            
            settled_data.append({
                "Status": status_emoji,
                "Contestant": contestant.name if contestant else "Unknown",
                "Amount": format_currency(bet.amount),
                "Outcome": bet.status.value.upper(),
                "Payout": format_currency(bet.payout),
                "ROI": f"{float(bet.roi):.1f}%"
            })
        
        df_settled = pd.DataFrame(settled_data)
        st.dataframe(df_settled, use_container_width=True, hide_index=True)
    else:
        st.info("No settled bets")


def render_leaderboard(market: PredictionMarket):
    """Render top bettors leaderboard."""
    st.header("🏆 LEADERBOARD")
    
    # Collect all users with their stats
    leaderboard_data = []
    for user_id, portfolio in market.user_portfolios.items():
        leaderboard_data.append({
            "User ID": user_id,
            "Wagered": float(portfolio.total_wagered),
            "Won": float(portfolio.total_won),
            "Lost": float(portfolio.total_lost),
            "ROI %": float(portfolio.roi_percentage),
            "Open Bets": portfolio.open_bets_count,
            "Referrals": portfolio.referral_count
        })
    
    df_leaderboard = pd.DataFrame(leaderboard_data)
    
    if len(df_leaderboard) > 0:
        # Sort by ROI or total won
        sort_by = st.radio("Sort by:", ["ROI %", "Won", "Wagered"], horizontal=True)
        df_leaderboard = df_leaderboard.sort_values(sort_by, ascending=False)
        
        # Add rank
        df_leaderboard.insert(0, "Rank", range(1, len(df_leaderboard) + 1))
        
        # Format currency columns
        for col in ["Wagered", "Won", "Lost"]:
            df_leaderboard[col] = df_leaderboard[col].apply(lambda x: f"${x:,.0f}")
        
        df_leaderboard["ROI %"] = df_leaderboard["ROI %"].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
    else:
        st.info("No users yet")


def render_revenue_metrics(market: PredictionMarket):
    """Render platform revenue and metrics."""
    st.header("💰 REVENUE METRICS")
    
    summary = market.get_market_summary()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Gross Merchandise Volume",
            format_currency(summary['gmv']),
            f"{summary['rake_percentage']:.2f}% of GMV"
        )
    
    with col2:
        st.metric("Platform Rake (5%)", format_currency(summary['total_rake_collected']))
    
    with col3:
        st.metric("Payouts Issued", format_currency(summary['total_payouts']))
    
    with col4:
        profit_margin = (float(summary['total_rake_collected']) - float(summary['total_payouts'])) if summary['total_payouts'] > 0 else 0
        st.metric("Net Profit", format_currency(profit_margin))
    
    st.divider()
    
    # Revenue visualization
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart: GMV breakdown
        fig_pie = go.Figure(data=[
            go.Pie(
                labels=['Rake Collected', 'Paid Out'],
                values=[
                    float(summary['total_rake_collected']),
                    float(summary['total_payouts'])
                ],
                marker=dict(colors=['#1f77b4', '#ff7f0e'])
            )
        ])
        fig_pie.update_layout(title="Rake vs Payouts", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Volume by contestant
        contestants_data = summary['contestants']
        if contestants_data:
            df_contestants = pd.DataFrame(contestants_data)
            fig_bar = px.bar(
                df_contestants,
                x='name',
                y='total_volume',
                title="Volume by Contestant",
                labels={'name': 'Contestant', 'total_volume': 'Volume ($)'},
                color='total_volume',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    # Detailed metrics table
    st.subheader("Contestant Performance")
    if summary['contestants']:
        df_contestants = pd.DataFrame(summary['contestants'])
        
        # Format display
        df_display = pd.DataFrame({
            "Contestant": df_contestants['name'],
            "Odds": df_contestants['odds'].apply(lambda x: f"{x:.2f}"),
            "Win Probability": df_contestants['implied_probability'].apply(lambda x: f"{x*100:.1f}%"),
            "Volume": df_contestants['total_volume'].apply(lambda x: f"${x:,.0f}"),
            "Bets": df_contestants['bets_placed']
        })
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def main():
    """Main dashboard application."""
    
    # Initialize market
    market = initialize_market()
    
    # Sidebar navigation
    st.sidebar.title("BeastBet Live 🎮")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigate",
        [
            "🔴 Live Odds",
            "🎯 Place Bet",
            "📊 Portfolio",
            "🏆 Leaderboard",
            "💰 Revenue"
        ]
    )
    
    # Market status
    st.sidebar.markdown("---")
    st.sidebar.subheader("Market Status")
    summary = market.get_market_summary()
    st.sidebar.metric("Total Volume", format_currency(summary['total_volume']))
    st.sidebar.metric("GMV", format_currency(summary['gmv']))
    st.sidebar.metric("Open Bets", summary['total_open_bets'])
    st.sidebar.metric("Users Active", len(market.user_portfolios))
    
    # Time
    st.sidebar.markdown("---")
    st.sidebar.text(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("BeastBet Live MVP - Production Ready")
    
    # Route pages
    if page == "🔴 Live Odds":
        render_live_odds_section(market)
    
    elif page == "🎯 Place Bet":
        render_betting_interface(market)
    
    elif page == "📊 Portfolio":
        render_portfolio_section(market)
    
    elif page == "🏆 Leaderboard":
        render_leaderboard(market)
    
    elif page == "💰 Revenue":
        render_revenue_metrics(market)
    
    # Footer
    st.markdown("---")
    st.caption("Built with Streamlit | BeastBet Live MVP")


if __name__ == "__main__":
    main()
