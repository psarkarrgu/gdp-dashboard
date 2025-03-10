import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def income_vs_expenses_chart(income_data: List[Dict], expense_data: List[Dict], period: str = "monthly"):
    """Create an income vs expenses chart"""
    if period == "monthly":
        # Convert to DataFrame
        income_df = pd.DataFrame(income_data)
        expense_df = pd.DataFrame(expense_data)
        
        # Merge data
        df = pd.merge(income_df, expense_df, on='date', how='outer').fillna(0)
        
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['income'],
            name='Income',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['expenses'],
            name='Expenses',
            marker_color='red'
        ))
        
        # Add savings line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['income'] - df['expenses'],
            mode='lines+markers',
            name='Savings',
            line=dict(color='blue', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Income vs Expenses',
            xaxis_title='Month',
            yaxis_title='Amount (₹)',
            barmode='group',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    elif period == "yearly":
        # Convert to DataFrame
        income_df = pd.DataFrame(income_data)
        expense_df = pd.DataFrame(expense_data)
        
        # Merge data
        df = pd.merge(income_df, expense_df, on='year', how='outer').fillna(0)
        
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['year'],
            y=df['income'],
            name='Income',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=df['year'],
            y=df['expenses'],
            name='Expenses',
            marker_color='red'
        ))
        
        # Add savings line
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df['income'] - df['expenses'],
            mode='lines+markers',
            name='Savings',
            line=dict(color='blue', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title='Yearly Income vs Expenses',
            xaxis_title='Year',
            yaxis_title='Amount (₹)',
            barmode='group',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    return None

def expense_breakdown_chart(expense_data: List[Dict], chart_type: str = "pie"):
    """Create an expense breakdown chart"""
    # Convert to DataFrame
    df = pd.DataFrame(expense_data)
    
    if chart_type == "pie":
        fig = px.pie(
            df, 
            values='amount', 
            names='category',
            title='Expense Breakdown by Category',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    elif chart_type == "bar":
        fig = px.bar(
            df,
            x='category',
            y='amount',
            title='Expense Breakdown by Category',
            color='category',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            xaxis_title='Category',
            yaxis_title='Amount (₹)',
            hovermode='x unified',
            xaxis={'categoryorder':'total descending'}
        )
        
        return fig
    
    return None

def budget_vs_actual_chart(budget_data: Dict):
    """Create a budget vs actual chart"""
    # Extract category data
    categories = []
    budget_amounts = []
    actual_amounts = []
    
    for category, data in budget_data["categories"].items():
        categories.append(category)
        budget_amounts.append(data["budget"])
        actual_amounts.append(data["actual"])
    
    # Create DataFrame
    df = pd.DataFrame({
        'category': categories,
        'budget': budget_amounts,
        'actual': actual_amounts
    })
    
    # Sort by budget amount
    df = df.sort_values('budget', ascending=False)
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['budget'],
        name='Budget',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['actual'],
        name='Actual',
        marker_color='red'
    ))
    
    # Update layout
    fig.update_layout(
        title='Budget vs Actual Spending by Category',
        xaxis_title='Category',
        yaxis_title='Amount (₹)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def net_worth_trend_chart(net_worth_data: List[Dict]):
    """Create a net worth trend chart"""
    # Convert to DataFrame
    df = pd.DataFrame(net_worth_data)
    
    # Create chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add assets and liabilities bars
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['assets'],
            name='Assets',
            marker_color='green'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['liabilities'],
            name='Liabilities',
            marker_color='red'
        ),
        secondary_y=False
    )
    
    # Add net worth line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['net_worth'],
            mode='lines+markers',
            name='Net Worth',
            line=dict(color='blue', width=3)
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title='Net Worth Trend',
        hovermode='x unified',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Amount (₹)', secondary_y=False)
    fig.update_yaxes(title_text='Net Worth (₹)', secondary_y=True)
    
    return fig

def asset_allocation_chart(allocation_data: Dict):
    """Create an asset allocation chart"""
    # Extract data
    categories = list(allocation_data["allocation"].keys())
    percentages = list(allocation_data["allocation"].values())
    
    # Create DataFrame
    df = pd.DataFrame({
        'category': categories,
        'percentage': percentages,
        'amount': [allocation_data["allocation_amount"][cat] for cat in categories]
    })
    
    # Create pie chart
    fig = px.pie(
        df, 
        values='percentage', 
        names='category',
        title='Asset Allocation',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data=['amount']
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Allocation: %{percent}<br>Amount: ₹%{customdata[0]:,.2f}'
    )
    
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def investment_performance_chart(investment_data: Dict):
    """Create an investment performance chart"""
    # Extract investment data
    investments = []
    absolute_returns = []
    annualized_returns = []
    
    for name, data in investment_data["investments"].items():
        investments.append(name)
        absolute_returns.append(data["absolute_return_percent"])
        annualized_returns.append(data["annualized_return_percent"])
    
    # Create DataFrame
    df = pd.DataFrame({
        'investment': investments,
        'absolute_return': absolute_returns,
        'annualized_return': annualized_returns
    })
    
    # Sort by absolute return
    df = df.sort_values('absolute_return', ascending=False)
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['investment'],
        y=df['absolute_return'],
        name='Total Return (%)',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=df['investment'],
        y=df['annualized_return'],
        name='Annualized Return (%)',
        marker_color='green'
    ))
    
    # Add horizontal line at 0%
    fig.add_shape(
        type='line',
        x0=-0.5,
        y0=0,
        x1=len(investments) - 0.5,
        y1=0,
        line=dict(
            color='red',
            width=2,
            dash='dash'
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Investment Performance',
        xaxis_title='Investment',
        yaxis_title='Return (%)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def goal_progress_chart(goal_data: Dict):
    """Create a goal progress chart"""
    # Extract goal data
    goals = []
    progress = []
    time_progress = []
    
    for name, data in goal_data.items():
        goals.append(name)
        progress.append(data["progress_percent"])
        time_progress.append(data["time_percent"])
    
    # Create DataFrame
    df = pd.DataFrame({
        'goal': goals,
        'progress': progress,
        'time_progress': time_progress
    })
    
    # Sort by progress
    df = df.sort_values('progress', ascending=False)
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['goal'],
        y=df['progress'],
        name='Financial Progress (%)',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=df['goal'],
        y=df['time_progress'],
        name='Time Elapsed (%)',
        marker_color='orange'
    ))
    
    # Update layout
    fig.update_layout(
        title='Financial Goal Progress',
        xaxis_title='Goal',
        yaxis_title='Progress (%)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def debt_breakdown_chart(debt_data: List[Dict]):
    """Create a debt breakdown chart"""
    # Convert to DataFrame
    df = pd.DataFrame(debt_data)
    
    # Create pie chart for debt distribution
    fig = px.pie(
        df, 
        values='remaining_amount', 
        names='name',
        title='Debt Breakdown',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Reds_r,
        hover_data=['debt_type', 'interest_rate', 'emi_amount']
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Type: %{customdata[0]}<br>Amount: ₹%{value:,.2f}<br>Interest Rate: %{customdata[1]}%<br>EMI: ₹%{customdata[2]:,.2f}'
    )
    
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def tax_comparison_chart(tax_data: Dict):
    """Create a chart comparing old and new tax regimes"""
    # Extract data
    categories = ['Gross Income', 'Taxable Income', 'Income Tax', 'Surcharge', 'Cess', 'Total Tax']
    old_regime_values = [
        tax_data["gross_income"],
        tax_data["old_regime"]["taxable_income"],
        tax_data["old_regime"]["tax"],
        tax_data["old_regime"]["surcharge"],
        tax_data["old_regime"]["cess"],
        tax_data["old_regime"]["total_tax"]
    ]
    new_regime_values = [
        tax_data["gross_income"],
        tax_data["new_regime"]["taxable_income"],
        tax_data["new_regime"]["tax"],
        tax_data["new_regime"]["surcharge"],
        tax_data["new_regime"]["cess"],
        tax_data["new_regime"]["total_tax"]
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'category': categories,
        'old_regime': old_regime_values,
        'new_regime': new_regime_values
    })
    
    # Create chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['old_regime'],
        name='Old Regime',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['new_regime'],
        name='New Regime',
        marker_color='green'
    ))
    
    # Update layout
    fig.update_layout(
        title='Tax Comparison: Old vs New Regime',
        xaxis_title='Category',
        yaxis_title='Amount (₹)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def deduction_breakdown_chart(deduction_data: Dict):
    """Create a chart showing tax deduction breakdown"""
    # Extract data
    categories = []
    amounts = []
    
    for category, amount in deduction_data.items():
        if amount > 0:  # Only include non-zero deductions
            categories.append(category)
            amounts.append(amount)
    
    # Create DataFrame
    df = pd.DataFrame({
        'category': categories,
        'amount': amounts
    })
    
    # Sort by amount
    df = df.sort_values('amount', ascending=False)
    
    # Create chart
    fig = px.bar(
        df,
        x='category',
        y='amount',
        title='Tax Deduction Breakdown',
        color='category',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis_title='Deduction Category',
        yaxis_title='Amount (₹)',
        hovermode='x unified',
        showlegend=False
    )
    
    return fig

def financial_health_gauge(health_score: float):
    """Create a gauge chart for financial health score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=health_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Financial Health Score"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'red'},
                {'range': [40, 60], 'color': 'orange'},
                {'range': [60, 80], 'color': 'yellow'},
                {'range': [80, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': health_score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    return fig

def loan_amortization_chart(amortization_data: Dict):
    """Create a loan amortization chart"""
    # Extract schedule data
    schedule = amortization_data["amortization_schedule"]
    
    months = [item["month"] for item in schedule]
    principal_payments = [item["principal_payment"] for item in schedule]
    interest_payments = [item["interest_payment"] for item in schedule]
    remaining_principals = [item["remaining_principal"] for item in schedule]
    
    # Create DataFrame
    df = pd.DataFrame({
        'month': months,
        'principal_payment': principal_payments,
        'interest_payment': interest_payments,
        'remaining_principal': remaining_principals
    })
    
    # Create subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add principal and interest payment bars
    fig.add_trace(
        go.Bar(
            x=df['month'],
            y=df['principal_payment'],
            name='Principal Payment',
            marker_color='blue'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Bar(
            x=df['month'],
            y=df['interest_payment'],
            name='Interest Payment',
            marker_color='red'
        ),
        secondary_y=False
    )
    
    # Add remaining principal line
    fig.add_trace(
        go.Scatter(
            x=df['month'],
            y=df['remaining_principal'],
            mode='lines',
            name='Remaining Principal',
            line=dict(color='green', width=2)
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title='Loan Amortization Schedule',
        barmode='stack',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text='Month')
    fig.update_yaxes(title_text='Monthly Payment (₹)', secondary_y=False)
    fig.update_yaxes(title_text='Remaining Principal (₹)', secondary_y=True)
    
    return fig

def retirement_projection_chart(retirement_data: Dict, current_age: int, retirement_age: int, life_expectancy: int):
    """Create a retirement projection chart"""
    # Calculate year range
    current_year = datetime.datetime.now().year
    years = list(range(current_year, current_year + (life_expectancy - current_age) + 1))
    ages = list(range(current_age, life_expectancy + 1))
    
    # Initialize corpus values
    corpus_values = [retirement_data["current_retirement_corpus"]]
    
    # Calculate corpus growth until retirement
    for _ in range(retirement_age - current_age):
        prev_corpus = corpus_values[-1]
        annual_contribution = retirement_data["monthly_contribution"] * 12
        # Assuming 8% annual return
        annual_return = (prev_corpus + annual_contribution / 2) * 0.08
        new_corpus = prev_corpus + annual_contribution + annual_return
        corpus_values.append(new_corpus)
    
    # Calculate corpus depletion after retirement
    annual_withdrawal = retirement_data["monthly_income_at_retirement"] * 12
    for _ in range(life_expectancy - retirement_age):
        prev_corpus = corpus_values[-1]
        # Assuming 6% annual return during retirement
        annual_return = prev_corpus * 0.06
        new_corpus = prev_corpus + annual_return - annual_withdrawal
        corpus_values.append(max(0, new_corpus))
    
    # Create DataFrame
    df = pd.DataFrame({
        'year': years,
        'age': ages,
        'corpus': corpus_values
    })
    
    # Create chart
    fig = go.Figure()
    
    # Add corpus line
    fig.add_trace(go.Scatter(
        x=df['age'],
        y=df['corpus'],
        mode='lines+markers',
        name='Retirement Corpus',
        line=dict(color='blue', width=3)
    ))
    
    # Add retirement age line
    fig.add_shape(
        type='line',
        x0=retirement_age,
        y0=0,
        x1=retirement_age,
        y1=max(corpus_values) * 1.1,
        line=dict(
            color='red',
            width=2,
            dash='dash'
        )
    )
    
    # Add annotation for retirement age
    fig.add_annotation(
        x=retirement_age,
        y=max(corpus_values) * 1.05,
        text=f"Retirement Age: {retirement_age}",
        showarrow=False,
        font=dict(
            color="red",
            size=12
        )
    )
    
    # Update layout
    fig.update_layout(
        title='Retirement Corpus Projection',
        xaxis_title='Age',
        yaxis_title='Corpus (₹)',
        hovermode='x',
        xaxis=dict(
            tickmode='linear',
            tick0=current_age,
            dtick=5
        )
    )
    
    return fig

def calendar_heatmap(event_data: List[Dict], year: int):
    """Create a calendar heatmap of financial events"""
    # Filter events for the year
    events = [event for event in event_data if event["event_date"].year == year]
    
    # Create a DataFrame with all days of the year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    delta = end_date - start_date
    
    dates = [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    df = pd.DataFrame({
        'date': dates,
        'count': 0,
        'events': [[] for _ in range(len(dates))]
    })
    
    # Populate with events
    for event in events:
        idx = (event["event_date"] - start_date).days
        if 0 <= idx < len(df):
            df.at[idx, 'count'] += 1
            df.at[idx, 'events'].append(event["title"])
    
    # Create heatmap
    df['weekday'] = df['date'].apply(lambda x: x.weekday())
    df['month'] = df['date'].apply(lambda x: x.month)
    df['day'] = df['date'].apply(lambda x: x.day)
    
    # Create the figure
    fig = px.density_heatmap(
        df, 
        x='day', 
        y='weekday',
        z='count',
        facet_col='month',
        facet_col_wrap=4,
        color_continuous_scale='Viridis',
        labels={
            'weekday': 'Day of Week',
            'day': 'Day of Month',
            'count': 'Number of Events'
        },
        title=f'Financial Calendar for {year}'
    )
    
    # Update y-axis labels
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    fig.update_yaxes(tickvals=list(range(7)), ticktext=weekday_labels)
    
    # Update x-axis labels for each subplot
    for i in range(1, 13):
        fig.update_xaxes(tickvals=[1, 15, 31], col=i)
    
    # Update facet labels to month names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for i, name in enumerate(month_names):
        fig.for_each_annotation(lambda a: a.update(text=name) if a.text == f'month={i+1}' else None)
    
    fig.update_layout(
        height=600,
        coloraxis_showscale=True
    )
    
    return fig